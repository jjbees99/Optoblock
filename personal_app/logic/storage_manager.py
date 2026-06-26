from pathlib import Path

from personal_app.data.database import Database


class StorageManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def export_json(self, target: str) -> None:
        self.db.export_json(Path(target))

    def import_json(self, source: str) -> None:
        self.db.import_json(Path(source))
