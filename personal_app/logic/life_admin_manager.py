from __future__ import annotations

from personal_app.data.database import Database


class LifeAdminManager:
    """Small shared CRUD layer for independent life-admin modules."""

    TABLES = {
        "bills": ("title", "amount", "due_date", "recurrence", "status", "notes"),
        "documents": ("title", "category", "note", "expiry_date", "location"),
        "errands": ("title", "event_at", "location", "priority", "status", "notes"),
        "follow_ups": ("contact", "reason", "method", "due_date", "status", "notes"),
        "travel_plans": ("title", "start_date", "end_date", "destination", "transport_notes", "checklist", "budget", "notes", "status"),
        "home_items": ("title", "category", "due_date", "repeat_option", "status", "notes"),
    }

    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self, table: str, archived: bool = False, search: str = "") -> list[dict]:
        self._columns(table)
        rows = self.db.all(f"SELECT * FROM {table} WHERE archived=? ORDER BY created_at DESC", (int(archived),))
        if search:
            needle = search.casefold()
            rows = [row for row in rows if needle in " ".join(str(v) for v in row.values()).casefold()]
        return rows

    def replace_active(self, table: str, rows: list[dict]) -> None:
        columns = self._columns(table)
        with self.db.connect() as conn:
            conn.execute(f"DELETE FROM {table} WHERE archived=0")
            names = ", ".join(columns)
            marks = ", ".join("?" for _ in columns)
            conn.executemany(f"INSERT INTO {table} ({names}) VALUES ({marks})", [tuple(row.get(c, "") for c in columns) for row in rows])

    def add(self, table: str, **values) -> int:
        columns = self._columns(table)
        supplied = [column for column in columns if column in values]
        return self.db.execute(
            f"INSERT INTO {table} ({', '.join(supplied)}) VALUES ({', '.join('?' for _ in supplied)})",
            tuple(values[column] for column in supplied),
        )

    def archive(self, table: str, item_id: int) -> None:
        self._columns(table)
        self.db.execute(f"UPDATE {table} SET archived=1 WHERE id=?", (item_id,))

    def restore(self, table: str, item_id: int) -> None:
        self._columns(table)
        self.db.execute(f"UPDATE {table} SET archived=0 WHERE id=?", (item_id,))

    def update_field(self, table: str, item_id: int, field: str, value: str) -> None:
        if field not in self._columns(table):
            raise ValueError("Unsupported field")
        self.db.execute(f"UPDATE {table} SET {field}=? WHERE id=?", (value, item_id))

    def _columns(self, table: str) -> tuple[str, ...]:
        if table not in self.TABLES:
            raise ValueError("Unsupported life-admin table")
        return self.TABLES[table]
