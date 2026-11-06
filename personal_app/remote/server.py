import asyncio
import logging
import socket
import sqlite3
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from personal_app.services.optoblock_service import NotFoundError, OptoblockService
from personal_app.data.database import APP_DIR

LOG = logging.getLogger("optoblock.remote")
STATIC = Path(__file__).parent / "static"
LOG_DIR = APP_DIR / "logs"
LOG_PATH = LOG_DIR / "phone-server.log"

def configure_file_logging() -> None:
    """Configure logging that is safe in a windowed (console-less) executable."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not any(isinstance(handler, RotatingFileHandler) for handler in LOG.handlers):
        handler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(threadName)s %(message)s"))
        LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)
    LOG.propagate = False

class TaskIn(BaseModel):
    name: str = Field(min_length=1, max_length=300); description: str = ""; category: str = ""; due_date: str = ""; priority: str = "Medium"
class TaskPatch(BaseModel):
    name: str | None = None; description: str | None = None; category: str | None = None; due_date: str | None = None; priority: str | None = None
class PlannerIn(BaseModel):
    plan_date: str; title: str = Field(min_length=1, max_length=300); start_minute: int = Field(ge=0, le=1430); duration_minutes: int = Field(default=30, ge=30, le=1440)
class ShoppingIn(BaseModel):
    name: str = Field(min_length=1, max_length=300); quantity: int = Field(default=1, ge=1, le=999); category: str = ""; list_type: str = "Grocery"
class NoteIn(BaseModel): title: str = "Untitled note"; body: str = ""
class BodyIn(BaseModel): body: str = Field(min_length=1, max_length=10000)

def create_app(service: OptoblockService) -> FastAPI:
    app = FastAPI(title="Optoblock Phone API", docs_url=None, redoc_url=None)
    configure_file_logging()

    @app.middleware("http")
    async def request_log(request, call_next):
        started = time.monotonic()
        try:
            response = await call_next(request)
        except Exception as exc:
            LOG.exception("%s %s failed type=%s", request.method, request.url.path, type(exc).__name__)
            raise
        LOG.info("%s %s status=%s duration_ms=%d", request.method, request.url.path,
                 response.status_code, (time.monotonic() - started) * 1000)
        return response
    clients: set[WebSocket] = set(); loop = None
    async def broadcast(domain, details):
        dead=[]
        for ws in tuple(clients):
            try: await ws.send_json({"type": f"{domain}.changed", **details})
            except Exception: dead.append(ws)
        clients.difference_update(dead)
    def changed(domain, details):
        if loop and loop.is_running(): asyncio.run_coroutine_threadsafe(broadcast(domain, details), loop)
    service.context.db.add_listener(changed)
    @app.on_event("startup")
    async def startup():
        nonlocal loop; loop = asyncio.get_running_loop()
    @app.get("/api/health")
    def health(): return {"status":"ok"}
    @app.get("/api/today")
    def today(): return service.today()
    @app.get("/api/tasks")
    def tasks(): return service.list_tasks()
    @app.post("/api/tasks", status_code=201)
    def add_task(body: TaskIn): return {"id": service.create_task(**body.model_dump())}
    @app.patch("/api/tasks/{item_id}")
    def edit_task(item_id:int, body:TaskPatch): return service.update_task(item_id, **body.model_dump(exclude_none=True))
    @app.post("/api/tasks/{item_id}/complete")
    def complete(item_id:int): service.complete_task(item_id); return {"ok":True}
    @app.post("/api/tasks/{item_id}/archive")
    def archive(item_id:int): service.archive_task(item_id); return {"ok":True}
    @app.get("/api/planner")
    def planner(date:str): return service.planner(date)
    @app.post("/api/planner", status_code=201)
    def add_planner(body:PlannerIn): return {"id":service.create_planner(**body.model_dump())}
    @app.patch("/api/planner/{item_id}")
    def edit_planner(item_id:int, body:dict): service.update_planner(item_id, **body); return {"ok":True}
    @app.delete("/api/planner/{item_id}")
    def delete_planner(item_id:int): service.delete_planner(item_id); return {"ok":True}
    @app.get("/api/shopping")
    def shopping(): return service.shopping()
    @app.post("/api/shopping", status_code=201)
    def add_shopping(body:ShoppingIn): return {"id":service.create_shopping(**body.model_dump())}
    @app.patch("/api/shopping/{item_id}")
    def edit_shopping(item_id:int, body:dict): return service.update_shopping(item_id, **body)
    @app.post("/api/shopping/{item_id}/toggle")
    def toggle(item_id:int): service.toggle_shopping(item_id); return {"ok":True}
    @app.delete("/api/shopping/{item_id}")
    def delete_shopping(item_id:int): service.delete_shopping(item_id); return {"ok":True}
    @app.get("/api/projects")
    def projects(): return service.projects()
    @app.post("/api/brain-dump", status_code=201)
    def brain(body:BodyIn): return {"id":service.add_brain_dump(body.body)}
    @app.get("/api/notes")
    def notes(): return service.notes()
    @app.get("/api/notes/{item_id}")
    def note(item_id:int): return service.note(item_id)
    @app.post("/api/notes", status_code=201)
    def add_note(body:NoteIn): return {"id":service.create_note(body.title, body.body)}
    @app.patch("/api/notes/{item_id}")
    def edit_note(item_id:int, body:NoteIn): service.update_note(item_id, body.title, body.body); return {"ok":True}
    @app.exception_handler(RequestValidationError)
    async def invalid(_request, exc):
        problems = [{"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
                    for error in exc.errors()]
        return JSONResponse(status_code=422, content={"error": "bad_input", "message": "Please check the highlighted information.", "details": problems})
    @app.exception_handler(NotFoundError)
    async def missing(_request, exc):
        return JSONResponse(status_code=404, content={"error": "not_found", "message": str(exc)})
    @app.exception_handler(sqlite3.OperationalError)
    async def database_error(_request, exc):
        if "locked" in str(exc).lower() or "busy" in str(exc).lower():
            return JSONResponse(status_code=503, content={"error": "database_busy", "message": "The Optoblock database is temporarily busy. Try again."})
        LOG.exception("Database operation failed")
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": "Optoblock could not complete the request."})
    @app.exception_handler(Exception)
    async def unexpected(_request, exc):
        LOG.exception("Unhandled phone API error type=%s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error": "internal_error", "message": "Optoblock could not complete the request."})
    @app.websocket("/ws/events")
    async def events(ws:WebSocket):
        await ws.accept(); clients.add(ws)
        try:
            while True: await ws.receive_text()
        except WebSocketDisconnect: clients.discard(ws)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    @app.get("/")
    def index(): return FileResponse(STATIC / "index.html")
    @app.get("/manifest.json")
    def manifest(): return FileResponse(STATIC / "manifest.json")
    @app.get("/service-worker.js")
    def worker(): return FileResponse(STATIC / "service-worker.js", media_type="application/javascript")
    return app

class PhoneServer:
    def __init__(self, service, host="127.0.0.1", port=8765):
        self.host=host; self.port=port; self.app=create_app(service); self.server=None; self.thread=None; self.error=""
    def start(self):
        configure_file_logging()
        LOG.info("Phone server starting; listening on http://%s:%s", self.host, self.port)
        with socket.socket() as sock:
            try: sock.bind((self.host,self.port))
            except OSError:
                self.error=f"Port {self.port} is already in use"
                LOG.exception("Phone server unavailable: %s", self.error)
                return False
        try:
            # Uvicorn's default formatter probes sys.stdout/sys.stderr.isatty(),
            # but those streams are None in the PyInstaller console=False build.
            config = uvicorn.Config(self.app, host=self.host, port=self.port,
                                    log_level="warning", workers=1,
                                    log_config=None, access_log=False)
            self.server = uvicorn.Server(config)
        except BaseException as exc:
            self.error = f"Phone server failed: {exc}"
            LOG.exception("Phone server configuration failed")
            return False
        def run():
            try:
                self.server.run()
            except BaseException as exc:
                self.error = f"Phone server failed: {exc}"
                LOG.exception("Unexpected phone server exception")
            finally:
                LOG.info("Phone server stopped")
        self.thread=threading.Thread(target=run, daemon=True, name="optoblock-phone-server")
        self.thread.start()
        LOG.info("Phone server thread started successfully")
        return True
    def stop(self, timeout=3):
        LOG.info("Phone server shutting down")
        if self.server: self.server.should_exit=True
        if self.thread: self.thread.join(timeout)
