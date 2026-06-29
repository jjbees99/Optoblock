from __future__ import annotations

from personal_app.data.database import Database


class BrainDumpManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self) -> list[dict]:
        return self.db.all("SELECT * FROM brain_dump WHERE archived=0 ORDER BY created_at DESC")

    def archived(self) -> list[dict]:
        return self.db.all("SELECT * FROM brain_dump WHERE archived=1 ORDER BY created_at DESC")

    def add(self, body: str) -> int:
        return self.db.execute("INSERT INTO brain_dump (body) VALUES (?)", (body.strip(),))

    def add_archived(self, body: str) -> int:
        return self.db.execute("INSERT INTO brain_dump (body, archived) VALUES (?, 1)", (body.strip(),))

    def archive(self, dump_id: int) -> None:
        self.db.execute("UPDATE brain_dump SET archived=1 WHERE id=?", (dump_id,))

    def restore(self, dump_id: int) -> None:
        self.db.execute("UPDATE brain_dump SET archived=0 WHERE id=?", (dump_id,))
