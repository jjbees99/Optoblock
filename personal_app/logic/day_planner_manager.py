from personal_app.data.database import Database

PLANNER_COLOURS = (
    "#7dd3fc",  # sky
    "#f9a8d4",  # pink
    "#86efac",  # green
    "#fdba74",  # orange
    "#c4b5fd",  # lilac
    "#fde68a",  # yellow
    "#5eead4",  # teal
    "#fca5a5",  # coral
)


class DayPlannerManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self, plan_date: str) -> list[dict]:
        return self.db.all("SELECT * FROM planner_blocks WHERE plan_date=? ORDER BY start_minute, id", (plan_date,))

    def add(self, plan_date: str, title: str, start: int, duration: int = 30) -> int:
        colour = self._next_colour(plan_date)
        return self.db.execute(
            "INSERT INTO planner_blocks(plan_date,title,start_minute,duration_minutes,colour) VALUES(?,?,?,?,?)",
            (plan_date, title, max(0, min(1430, start)), max(30, duration), colour),
        )

    def _next_colour(self, plan_date: str) -> str:
        rows = self.db.all("SELECT colour FROM planner_blocks WHERE plan_date=? ORDER BY id", (plan_date,))
        used = [row["colour"] for row in rows]
        for colour in PLANNER_COLOURS:
            if colour not in used:
                return colour
        return PLANNER_COLOURS[len(rows) % len(PLANNER_COLOURS)]

    def ensure_varied_colours(self) -> None:
        """Spread legacy default-blue blocks across the palette once, without touching customised colours."""
        dates = self.db.all(
            "SELECT plan_date FROM planner_blocks GROUP BY plan_date HAVING COUNT(*) > 1 AND COUNT(DISTINCT colour) = 1"
        )
        for date_row in dates:
            rows = self.db.all("SELECT id FROM planner_blocks WHERE plan_date=? ORDER BY start_minute, id", (date_row["plan_date"],))
            with self.db.connect() as conn:
                conn.executemany(
                    "UPDATE planner_blocks SET colour=? WHERE id=?",
                    [(PLANNER_COLOURS[index % len(PLANNER_COLOURS)], row["id"]) for index, row in enumerate(rows)],
                )
                conn.commit()

    def update(self, block_id: int, **values) -> None:
        allowed = {"title", "start_minute", "duration_minutes", "notes", "colour"}
        values = {key: value for key, value in values.items() if key in allowed}
        if not values: return
        assignments = ", ".join(f"{key}=?" for key in values)
        self.db.execute(f"UPDATE planner_blocks SET {assignments} WHERE id=?", (*values.values(), block_id))

    def delete(self, block_id: int) -> None:
        self.db.execute("DELETE FROM planner_blocks WHERE id=?", (block_id,))

    def duplicate(self, block_id: int) -> None:
        row = self.db.one("SELECT * FROM planner_blocks WHERE id=?", (block_id,))
        if row: self.add(row["plan_date"], row["title"], min(1430, row["start_minute"] + row["duration_minutes"]), row["duration_minutes"])
