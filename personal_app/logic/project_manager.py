from personal_app.data.database import Database
from personal_app.logic.task_manager import TaskManager


class ProjectManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self, include_archived: bool = False, search: str = "") -> list[dict]:
        rows = self.db.all("SELECT * FROM projects ORDER BY created_at DESC")
        if not include_archived:
            rows = [row for row in rows if row["status"] != "Archived"]
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in " ".join(str(v).lower() for v in row.values())]
        return rows

    def add(self, title: str, description: str = "", category: str = "", status: str = "Idea", next_action: str = "") -> int:
        return self.db.execute(
            "INSERT INTO projects (title, description, category, status, next_action) VALUES (?, ?, ?, ?, ?)",
            (title, description, category, status, next_action),
        )

    def update(self, project_id: int, title: str, description: str, category: str, status: str, next_action: str, done: bool) -> None:
        self.db.execute(
            "UPDATE projects SET title=?, description=?, category=?, status=?, next_action=?, next_action_done=? WHERE id=?",
            (title, description, category, status, next_action, int(done), project_id),
        )

    def archive(self, project_id: int) -> None:
        self.db.execute("UPDATE projects SET status='Archived' WHERE id=?", (project_id,))

    def delete(self, project_id: int) -> None:
        self.db.execute("DELETE FROM projects WHERE id=?", (project_id,))

    def convert_next_action(self, project_id: int, tasks: TaskManager) -> None:
        row = self.db.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if row and row["next_action"]:
            tasks.add(row["next_action"], f"From project: {row['title']}", row["category"], "", "Medium")
            self.db.execute("UPDATE projects SET next_action_done=1 WHERE id=?", (project_id,))

    def next_action(self) -> str:
        row = self.db.one(
            "SELECT title, next_action FROM projects WHERE status NOT IN ('Archived','Completed') AND next_action != '' AND next_action_done=0 ORDER BY created_at DESC LIMIT 1"
        )
        return f"{row['title']}: {row['next_action']}" if row else "No project action queued."

    def in_progress_count(self) -> int:
        return self.db.one("SELECT COUNT(*) AS c FROM projects WHERE status='In Progress'")["c"]
