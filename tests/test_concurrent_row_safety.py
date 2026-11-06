import tempfile, threading, unittest
from pathlib import Path
from personal_app.data.database import Database
from personal_app.logic.task_manager import TaskManager

class ConcurrentRowSafetyTests(unittest.TestCase):
    def test_unrelated_phone_row_survives_desktop_row_update(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Database(Path(directory)/'db.sqlite3'); db.initialize(); tasks=TaskManager(db)
            a=tasks.add('A'); tasks.add('B'); phone=tasks.add('C')
            tasks.update(a,'A edited','','','','Medium')
            self.assertEqual({'A edited','B','C'},{x['name'] for x in tasks.list()})
            self.assertTrue(db.one('SELECT id FROM tasks WHERE id=?',(phone,)))
            db.checkpoint()
    def test_near_simultaneous_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Database(Path(directory)/'db.sqlite3'); db.initialize(); tasks=TaskManager(db)
            threads=[threading.Thread(target=lambda i=i: tasks.add(f'T{i}')) for i in range(12)]
            [t.start() for t in threads]; [t.join() for t in threads]
            self.assertEqual(12,len(tasks.list()))
            db.checkpoint()
