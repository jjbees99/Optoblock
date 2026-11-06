from datetime import date


class NotFoundError(LookupError):
    pass


class OptoblockService:
    """Interface-neutral application actions shared by desktop and remote clients."""
    def __init__(self, context): self.context = context

    def today(self):
        today = date.today().isoformat(); tasks = self.context.tasks.list("Active")
        return {"date": today, "daily_focus": self.context.settings.get("daily_focus") or "",
                "planner": self.context.day_planner.list(today), "tasks": tasks,
                "shopping_count": self.context.shopping.stats()["grocery"] + self.context.shopping.stats()["amazon"],
                "active_project_count": self.context.projects.in_progress_count()}

    def list_tasks(self): return self.context.tasks.list("Active")
    def create_task(self, **data): return self.context.tasks.add(**data)
    def update_task(self, item_id, **data):
        row = self.context.db.one("SELECT * FROM tasks WHERE id=?", (item_id,))
        if not row: raise NotFoundError("Task not found")
        values = {**row, **data}; self.context.tasks.update(item_id, values["name"], values["description"], values["category"], values["due_date"], values["priority"])
        if "status" in data:
            self.context.db.execute("UPDATE tasks SET status=? WHERE id=?", (data["status"], item_id))
        return self.context.db.one("SELECT * FROM tasks WHERE id=?", (item_id,))
    def complete_task(self, item_id, done=True):
        if not self.context.db.one("SELECT id FROM tasks WHERE id=?", (item_id,)): raise NotFoundError("Task not found")
        self.context.tasks.complete(item_id, done)
    def archive_task(self, item_id):
        if not self.context.db.one("SELECT id FROM tasks WHERE id=?", (item_id,)): raise NotFoundError("Task not found")
        self.context.tasks.archive(item_id)

    def planner(self, day): return self.context.day_planner.list(day)
    def create_planner(self, **data): return self.context.day_planner.add(data["plan_date"], data["title"], data["start_minute"], data.get("duration_minutes", 30))
    def update_planner(self, item_id, **data):
        if not self.context.db.one("SELECT id FROM planner_blocks WHERE id=?", (item_id,)): raise NotFoundError("Planner block not found")
        self.context.day_planner.update(item_id, **data)
    def delete_planner(self, item_id): self.context.day_planner.delete(item_id)

    def shopping(self): return self.context.shopping.list()
    def create_shopping(self, **data): return self.context.shopping.add(**data)
    def update_shopping(self, item_id, **data):
        row = self.context.db.one("SELECT * FROM shopping_items WHERE id=?", (item_id,))
        if not row: raise NotFoundError("Shopping item not found")
        allowed = {k: v for k, v in data.items() if k in {"name", "quantity", "category", "list_type", "bought"}}
        if allowed:
            sql = ", ".join(f"{k}=?" for k in allowed); self.context.db.execute(f"UPDATE shopping_items SET {sql} WHERE id=?", (*allowed.values(), item_id))
        return self.context.db.one("SELECT * FROM shopping_items WHERE id=?", (item_id,))
    def toggle_shopping(self, item_id):
        row = self.context.db.one("SELECT bought FROM shopping_items WHERE id=?", (item_id,))
        if not row: raise NotFoundError("Shopping item not found")
        self.context.shopping.set_bought(item_id, not row["bought"])
    def delete_shopping(self, item_id): self.context.shopping.delete(item_id)

    def projects(self): return self.context.projects.list()
    def add_brain_dump(self, body): return self.context.brain_dump.add(body)
    def notes(self): return self.context.notes.list()
    def note(self, item_id):
        row = self.context.notes.get(item_id)
        if not row: raise NotFoundError("Note not found")
        return row
    def create_note(self, title="Untitled note", body=""):
        item_id = self.context.notes.create(); self.context.notes.save(item_id, title, body); return item_id
    def update_note(self, item_id, title, body): self.note(item_id); self.context.notes.save(item_id, title, body)
