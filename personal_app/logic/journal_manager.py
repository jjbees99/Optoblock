from __future__ import annotations

from datetime import date

from personal_app.data.database import Database


class JournalManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry_type: str, title: str = "", body: str = "", drawing: bytes | None = None) -> int:
        return self.db.execute(
            "INSERT INTO journal_entries (entry_date, entry_type, title, body, drawing) VALUES (?, ?, ?, ?, ?)",
            (date.today().isoformat(), entry_type, title.strip(), body.strip(), drawing),
        )

    def list(self) -> list[dict]:
        return self.db.all("SELECT * FROM journal_entries ORDER BY entry_date DESC, created_at DESC, id DESC")

    def get(self, entry_id: int) -> dict | None:
        return self.db.one("SELECT * FROM journal_entries WHERE id=?", (entry_id,))

    def delete(self, entry_id: int) -> None:
        self.db.execute("DELETE FROM journal_entries WHERE id=?", (entry_id,))

    def completed_today(self) -> bool:
        return self.db.one("SELECT id FROM journal_entries WHERE entry_date=? LIMIT 1", (date.today().isoformat(),)) is not None
