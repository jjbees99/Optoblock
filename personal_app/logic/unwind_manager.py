import random

from personal_app.data.database import Database


DEFAULT_UNWIND = [
    ("Go for a walk", "physical", "30 min"),
    ("Stretch", "recovery", "15 min"),
    ("Read a chapter", "low energy", "30 min"),
    ("Watch an episode guilt-free", "low energy", "1 hour+"),
    ("Sketch or CAD a small idea", "creative", "30 min"),
    ("Make a quick generative art piece", "creative", "30 min"),
    ("Cook something properly", "recovery", "1 hour+"),
    ("Clean one small area", "physical", "15 min"),
    ("Journal for 5 minutes", "recovery", "5 min"),
    ("Listen to music without scrolling", "low energy", "15 min"),
]


class UnwindManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def ensure_defaults(self) -> None:
        count = self.db.one("SELECT COUNT(*) AS c FROM unwind_items")["c"]
        if count == 0:
            self.db.execute_many(
                "INSERT INTO unwind_items (name, activity_type, estimated_time) VALUES (?, ?, ?)",
                DEFAULT_UNWIND,
            )

    def list(self, search: str = "") -> list[dict]:
        rows = self.db.all("SELECT * FROM unwind_items ORDER BY done_today, activity_type, name")
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in " ".join(str(v).lower() for v in row.values())]
        return rows

    def add(self, name: str, activity_type: str = "recovery", estimated_time: str = "15 min") -> int:
        return self.db.execute(
            "INSERT INTO unwind_items (name, activity_type, estimated_time) VALUES (?, ?, ?)",
            (name, activity_type, estimated_time),
        )

    def set_done(self, item_id: int, done: bool) -> None:
        self.db.execute("UPDATE unwind_items SET done_today=? WHERE id=?", (int(done), item_id))

    def reset_daily(self) -> None:
        self.db.execute("UPDATE unwind_items SET done_today=0")

    def delete(self, item_id: int) -> None:
        self.db.execute("DELETE FROM unwind_items WHERE id=?", (item_id,))

    def suggest(self, activity_type: str = "Any", estimated_time: str = "Any") -> dict | None:
        rows = [row for row in self.list() if not row["done_today"]]
        if activity_type != "Any":
            rows = [row for row in rows if row["activity_type"] == activity_type]
        if estimated_time != "Any":
            rows = [row for row in rows if row["estimated_time"] == estimated_time]
        return random.choice(rows) if rows else None
