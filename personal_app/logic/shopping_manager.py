from personal_app.data.database import Database


class ShoppingManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self, list_type: str | None = None, include_archived: bool = False, search: str = "") -> list[dict]:
        rows = self.db.all("SELECT * FROM shopping_items ORDER BY bought, list_type, category, name")
        if list_type:
            rows = [row for row in rows if row["list_type"] == list_type]
        if not include_archived:
            rows = [row for row in rows if not row["archived"]]
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in " ".join(str(v).lower() for v in row.values())]
        return rows

    def add(self, name: str, quantity: int = 1, category: str = "", list_type: str = "Grocery") -> int:
        existing = self.db.one(
            "SELECT * FROM shopping_items WHERE lower(name)=lower(?) AND list_type=? AND archived=0",
            (name.strip(), list_type),
        )
        if existing:
            self.db.execute("UPDATE shopping_items SET quantity=quantity+? WHERE id=?", (max(1, quantity), existing["id"]))
            return int(existing["id"])
        return self.db.execute(
            "INSERT INTO shopping_items (name, quantity, category, list_type) VALUES (?, ?, ?, ?)",
            (name.strip(), max(1, quantity), category, list_type),
        )

    def set_bought(self, item_id: int, bought: bool) -> None:
        self.db.execute("UPDATE shopping_items SET bought=? WHERE id=?", (int(bought), item_id))

    def move(self, item_id: int) -> None:
        row = self.db.one("SELECT list_type FROM shopping_items WHERE id=?", (item_id,))
        if row:
            target = "Amazon" if row["list_type"] == "Grocery" else "Grocery"
            self.db.execute("UPDATE shopping_items SET list_type=? WHERE id=?", (target, item_id))

    def clear_bought(self) -> None:
        self.db.execute("DELETE FROM shopping_items WHERE bought=1")

    def archive_bought(self) -> None:
        self.db.execute("UPDATE shopping_items SET archived=1 WHERE bought=1")

    def delete(self, item_id: int) -> None:
        self.db.execute("DELETE FROM shopping_items WHERE id=?", (item_id,))

    def email_body(self) -> str:
        lines = ["Shopping List", ""]
        for list_type in ("Grocery", "Amazon"):
            rows = [row for row in self.list(list_type) if not row["bought"]]
            lines.append(f"{list_type}")
            lines.append("-" * len(list_type))
            if rows:
                for row in rows:
                    category = f" ({row['category']})" if row["category"] else ""
                    lines.append(f"- {row['quantity']} x {row['name']}{category}")
            else:
                lines.append("- Nothing needed")
            lines.append("")
        return "\n".join(lines).strip()

    def stats(self) -> dict:
        grocery = self.db.one("SELECT COUNT(*) AS c FROM shopping_items WHERE list_type='Grocery' AND bought=0 AND archived=0")["c"]
        amazon = self.db.one("SELECT COUNT(*) AS c FROM shopping_items WHERE list_type='Amazon' AND bought=0 AND archived=0")["c"]
        bought = self.db.one("SELECT COUNT(*) AS c FROM shopping_items WHERE bought=1")["c"]
        return {"grocery": grocery, "amazon": amazon, "bought": bought}
