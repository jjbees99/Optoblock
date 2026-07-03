from __future__ import annotations

import re
from pathlib import Path

from personal_app.data.database import DATA_DIR, Database


class NotesManager:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.notes_dir = DATA_DIR / "notes"

    def list(self) -> list[dict]:
        return self.db.all("SELECT * FROM notes ORDER BY updated_at DESC, id DESC")

    def get(self, note_id: int) -> dict | None:
        return self.db.one("SELECT * FROM notes WHERE id=?", (note_id,))

    def create(self) -> int:
        return self.db.execute("INSERT INTO notes (title, body) VALUES ('Untitled note', '')")

    def save(self, note_id: int, title: str, body: str) -> None:
        self.db.execute(
            "UPDATE notes SET title=?, body=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title.strip() or "Untitled note", body, note_id),
        )
        self._write_text(note_id, title, body)

    def delete(self, note_id: int) -> None:
        for path in self.notes_dir.glob(f"{note_id}-*.txt") if self.notes_dir.exists() else []:
            path.unlink(missing_ok=True)
        self.db.execute("DELETE FROM notes WHERE id=?", (note_id,))

    def _write_text(self, note_id: int, title: str, body: str) -> None:
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        for old in self.notes_dir.glob(f"{note_id}-*.txt"):
            old.unlink(missing_ok=True)
        safe = re.sub(r"[^A-Za-z0-9._ -]+", "", title).strip()[:60] or "Untitled note"
        target = self.notes_dir / f"{note_id}-{safe}.txt"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(body, encoding="utf-8")
        temporary.replace(target)
