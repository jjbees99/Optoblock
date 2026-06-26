from __future__ import annotations

from datetime import date, datetime, timedelta

from personal_app.data.database import Database


class TaskManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self, filter_name: str = "All", search: str = "") -> list[dict]:
        rows = self.db.all("SELECT * FROM tasks ORDER BY status, priority DESC, due_date, created_at DESC")
        if filter_name == "Active":
            rows = [row for row in rows if row["status"] == "Active"]
        elif filter_name == "Completed":
            rows = [row for row in rows if row["status"] == "Completed"]
        elif filter_name == "Archived":
            rows = [row for row in rows if row["status"] == "Archived"]
        elif filter_name == "High priority":
            rows = [row for row in rows if row["priority"] == "High" and row["status"] != "Archived"]
        elif filter_name == "Due soon":
            soon = date.today() + timedelta(days=3)
            rows = [row for row in rows if row["due_date"] and row["status"] == "Active" and _date(row["due_date"]) <= soon]
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in " ".join(str(v).lower() for v in row.values())]
        return rows

    def add(self, name: str, description: str = "", category: str = "", due_date: str = "", priority: str = "Medium") -> int:
        return self.db.execute(
            "INSERT INTO tasks (name, description, category, due_date, priority) VALUES (?, ?, ?, ?, ?)",
            (name, description, category, due_date, priority),
        )

    def update(self, task_id: int, name: str, description: str, category: str, due_date: str, priority: str) -> None:
        self.db.execute(
            "UPDATE tasks SET name=?, description=?, category=?, due_date=?, priority=? WHERE id=?",
            (name, description, category, due_date, priority, task_id),
        )

    def complete(self, task_id: int, done: bool) -> None:
        status = "Completed" if done else "Active"
        completed_at = datetime.now().isoformat(timespec="seconds") if done else ""
        self.db.execute("UPDATE tasks SET status=?, completed_at=? WHERE id=?", (status, completed_at, task_id))

    def archive(self, task_id: int) -> None:
        self.db.execute("UPDATE tasks SET status='Archived' WHERE id=?", (task_id,))

    def restore(self, task_id: int) -> None:
        self.db.execute("UPDATE tasks SET status='Active', completed_at='' WHERE id=?", (task_id,))

    def archive_completed(self) -> None:
        self.db.execute("UPDATE tasks SET status='Archived' WHERE status='Completed'")

    def delete(self, task_id: int) -> None:
        self.db.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    def replace_all(self, rows: list[dict]) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM tasks")
            conn.executemany(
                """
                INSERT INTO tasks (name, description, category, due_date, priority, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.get("name", ""),
                        row.get("description", ""),
                        row.get("category", ""),
                        row.get("due_date", ""),
                        row.get("priority", "Medium"),
                        row.get("status", "Active"),
                        row.get("completed_at", ""),
                    )
                    for row in rows
                ],
            )
            conn.commit()

    def stats(self) -> dict:
        active = self.db.one("SELECT COUNT(*) AS c FROM tasks WHERE status='Active'")["c"]
        completed = self.db.one("SELECT COUNT(*) AS c FROM tasks WHERE status='Completed'")["c"]
        high = self.db.all("SELECT * FROM tasks WHERE priority='High' AND status='Active' ORDER BY due_date LIMIT 5")
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_done = self.db.one(
            "SELECT COUNT(*) AS c FROM tasks WHERE completed_at >= ?",
            (week_start.isoformat(),),
        )["c"]
        return {"active": active, "completed": completed, "high": high, "week_done": week_done}


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return date.max
