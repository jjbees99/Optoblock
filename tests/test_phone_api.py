import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from personal_app.app import AppContext
from personal_app.data.database import DB_PATH, Database
from personal_app.remote.server import PhoneServer, create_app


class PhoneApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); db = Database(Path(self.tmp.name) / "test.sqlite3"); db.initialize(); self.db = db
        self.context = AppContext.create.__func__(AppContext) if False else None
        from personal_app.logic.task_manager import TaskManager
        from personal_app.logic.shopping_manager import ShoppingManager
        from personal_app.logic.project_manager import ProjectManager
        from personal_app.logic.day_planner_manager import DayPlannerManager
        from personal_app.logic.brain_dump_manager import BrainDumpManager
        from personal_app.logic.notes_manager import NotesManager
        from personal_app.logic.settings_manager import SettingsManager
        class C: pass
        c=C(); c.db=db; c.tasks=TaskManager(db); c.shopping=ShoppingManager(db); c.projects=ProjectManager(db); c.day_planner=DayPlannerManager(db); c.brain_dump=BrainDumpManager(db); c.notes=NotesManager(db); c.settings=SettingsManager(db)
        from personal_app.services.optoblock_service import OptoblockService
        self.service = OptoblockService(c)
        self.client=TestClient(create_app(self.service))
        self.assertNotEqual(self.db.path.resolve(), DB_PATH.resolve())
    def tearDown(self):
        self.client.close(); self.db.checkpoint(); self.context = None; self.tmp.cleanup()
    def test_health_and_crud(self):
        before = self.db.one('SELECT COUNT(*) AS count FROM brain_dump')['count']
        self.assertEqual(self.client.get('/api/health').json(), {'status':'ok'})
        self.assertEqual(self.db.one('SELECT COUNT(*) AS count FROM brain_dump')['count'], before)
        item=self.client.post('/api/tasks',json={'name':'Phone task'}).json()['id']
        self.assertTrue(any(x['id']==item for x in self.client.get('/api/tasks').json()))
        self.assertEqual(self.client.post(f'/api/tasks/{item}/complete').status_code,200)
    def test_bad_input_is_structured_422(self):
        response=self.client.post('/api/shopping',json={'name':'','quantity':0})
        self.assertEqual(response.status_code,422)
        self.assertEqual(response.json()['error'], 'bad_input')
        self.assertIn('message', response.json())
    def test_all_mobile_create_actions(self):
        cases = [
            ('/api/tasks', {'name': 'Mobile task'}),
            ('/api/shopping', {'name': 'Mobile shopping'}),
            ('/api/brain-dump', {'body': 'Mobile thought'}),
            ('/api/planner', {'title': 'Mobile plan', 'plan_date': '2026-08-22', 'start_minute': 540, 'duration_minutes': 30}),
            ('/api/notes', {'title': 'Mobile note'}),
        ]
        for endpoint, payload in cases:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(endpoint, json=payload)
                self.assertEqual(response.status_code, 201, response.text)
                self.assertIsInstance(response.json()['id'], int)
    def test_task_requires_a_nonempty_name(self):
        response = self.client.post('/api/tasks', json={'name': ''})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error'], 'bad_input')

    def test_server_config_does_not_require_console_streams(self):
        server = PhoneServer(self.service, port=0)
        with patch("sys.stdout", None), patch("sys.stderr", None):
            self.assertTrue(server.start())
        self.assertIsNone(server.server.config.log_config)
        self.assertFalse(server.server.config.access_log)
        server.stop()
