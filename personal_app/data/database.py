import base64
import json
import sqlite3
import os
import re
import shutil
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


LEGACY_APP_DIR = Path.home() / ("." + "momen" + "tum")
LEGACY_DB_PATH = LEGACY_APP_DIR / ("momen" + "tum.sqlite3")
APP_DIR = Path.home() / ".optoblock"
DB_PATH = APP_DIR / "optoblock.sqlite3"
DATA_DIR = APP_DIR / "data"


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self._write_lock = threading.RLock()
        self._listeners: list = []
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path == DB_PATH and not self.path.exists() and LEGACY_DB_PATH.exists():
            self.path.write_bytes(LEGACY_DB_PATH.read_bytes())

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        with self._write_lock, self.connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    due_date TEXT DEFAULT '',
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'Active',
                    completed_at TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    status TEXT DEFAULT 'Idea',
                    next_action TEXT DEFAULT '',
                    next_action_done INTEGER DEFAULT 0,
                    progress_colour TEXT DEFAULT 'Red',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    category TEXT DEFAULT '',
                    bought INTEGER DEFAULT 0,
                    list_type TEXT DEFAULT 'Grocery',
                    archived INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    ingredients TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS unwind_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    activity_type TEXT DEFAULT 'recovery',
                    estimated_time TEXT DEFAULT '15 min',
                    done_today INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS brain_dump (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    body TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    archived INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS finance_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT DEFAULT '',
                    entry_type TEXT DEFAULT 'Expense',
                    category TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    amount REAL DEFAULT 0,
                    account TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, amount REAL DEFAULT 0,
                    due_date TEXT DEFAULT '', recurrence TEXT DEFAULT 'One-off', status TEXT DEFAULT 'Upcoming',
                    notes TEXT DEFAULT '', archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT DEFAULT 'Other',
                    note TEXT DEFAULT '', expiry_date TEXT DEFAULT '', location TEXT DEFAULT '',
                    archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS errands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, event_at TEXT DEFAULT '',
                    location TEXT DEFAULT '', priority TEXT DEFAULT 'Medium', status TEXT DEFAULT 'Not started',
                    notes TEXT DEFAULT '', archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS follow_ups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, contact TEXT NOT NULL, reason TEXT DEFAULT '',
                    method TEXT DEFAULT 'Email', due_date TEXT DEFAULT '', status TEXT DEFAULT 'Needs reply',
                    notes TEXT DEFAULT '', archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS travel_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, start_date TEXT DEFAULT '',
                    end_date TEXT DEFAULT '', destination TEXT DEFAULT '', transport_notes TEXT DEFAULT '',
                    checklist TEXT DEFAULT '[]', budget REAL DEFAULT 0, notes TEXT DEFAULT '',
                    status TEXT DEFAULT 'Active', archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS home_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT DEFAULT 'Other',
                    due_date TEXT DEFAULT '', repeat_option TEXT DEFAULT '', status TEXT DEFAULT 'Not started',
                    notes TEXT DEFAULT '', archived INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT NOT NULL,
                    entry_type TEXT DEFAULT 'Diary',
                    title TEXT DEFAULT '',
                    body TEXT DEFAULT '',
                    drawing BLOB,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT DEFAULT '', body TEXT DEFAULT '',
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS planner_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    start_minute INTEGER NOT NULL,
                    duration_minutes INTEGER NOT NULL DEFAULT 30,
                    notes TEXT DEFAULT '',
                    colour TEXT DEFAULT '#7dd3fc',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_planner_blocks_date ON planner_blocks(plan_date, start_minute);
                """
            )
            self._ensure_column(conn, "projects", "progress_colour", "TEXT DEFAULT 'Red'")

    def add_listener(self, listener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def checkpoint(self) -> None:
        """Release WAL files before shutdown or temporary-database cleanup."""
        with self._write_lock, self.connect() as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def notify(self, domain: str, details: dict | None = None) -> None:
        for listener in tuple(self._listeners):
            try:
                listener(domain, details or {})
            except Exception:
                pass

    @staticmethod
    def _domain_for_query(query: str) -> str:
        match = re.search(r"(?:into|update|from)\s+([a-z_]+)", query, re.I)
        table = match.group(1) if match else "data"
        return {"shopping_items": "shopping", "planner_blocks": "planner", "brain_dump": "brain_dump",
                "finance_entries": "finance", "journal_entries": "journal", "unwind_items": "unwind",
                "follow_ups": "follow_up", "travel_plans": "travel", "home_items": "home"}.get(table, table)

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def all(self, query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]

    def one(self, query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        rows = self.all(query, params)
        return rows[0] if rows else None

    def execute(self, query: str, params: Iterable[Any] = ()) -> int:
        with self._write_lock:
            with self.connect() as conn:
                cur = conn.execute(query, tuple(params))
                conn.commit()
                row_id = int(cur.lastrowid)
            self.write_readable_snapshot()
        self.notify(self._domain_for_query(query))
        return row_id

    def execute_many(self, query: str, rows: Iterable[Iterable[Any]]) -> None:
        with self._write_lock:
            with self.connect() as conn:
                conn.executemany(query, rows)
                conn.commit()
            self.write_readable_snapshot()
        self.notify(self._domain_for_query(query))

    def write_readable_snapshot(self) -> None:
        """Atomically maintain a human-readable companion backup to SQLite."""
        with self._write_lock:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            target = DATA_DIR / "optoblock-data.json"
            temporary = target.with_suffix(".tmp")
            tables = [row["name"] for row in self.all(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )]
            payload = {table: self.all(f"SELECT * FROM {table}") for table in tables}
            for rows in payload.values():
                for row in rows:
                    for key, value in row.items():
                        if isinstance(value, bytes):
                            row[key] = {"__bytes__": base64.b64encode(value).decode("ascii")}
            temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(temporary, target)

    def export_json(self, target: Path) -> None:
        tables = [row["name"] for row in self.all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        payload = {table: self.all(f"SELECT * FROM {table}") for table in tables}
        for rows in payload.values():
            for row in rows:
                for key, value in row.items():
                    if isinstance(value, bytes):
                        row[key] = {"__bytes__": base64.b64encode(value).decode("ascii")}
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_json(self, source: Path) -> None:
        payload = json.loads(source.read_text(encoding="utf-8"))
        with self.connect() as conn:
            valid_tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table, rows in payload.items():
                if table not in valid_tables:
                    continue
                if not rows:
                    continue
                conn.execute(f"DELETE FROM {table}")
                columns = list(rows[0].keys())
                placeholders = ", ".join("?" for _ in columns)
                col_sql = ", ".join(columns)
                values = [
                    tuple(
                        base64.b64decode(value["__bytes__"])
                        if isinstance((value := row.get(col)), dict) and "__bytes__" in value
                        else value
                        for col in columns
                    )
                    for row in rows
                ]
                conn.executemany(f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})", values)
            conn.commit()
