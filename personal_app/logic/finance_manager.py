from __future__ import annotations

from personal_app.data.database import Database


class FinanceManager:
    def __init__(self, db: Database) -> None:
        self.db = db

    def list(self) -> list[dict]:
        return self.db.all("SELECT * FROM finance_entries ORDER BY entry_date DESC, id DESC")

    def replace_all(self, rows: list[dict]) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM finance_entries")
            conn.executemany(
                """
                INSERT INTO finance_entries (entry_date, entry_type, category, description, amount, account)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row.get("entry_date", ""),
                        row.get("entry_type", "Expense"),
                        row.get("category", ""),
                        row.get("description", ""),
                        float(row.get("amount") or 0),
                        row.get("account", ""),
                    )
                    for row in rows
                ],
            )
            conn.commit()

    def totals(self) -> dict:
        rows = self.list()
        income = sum(float(row["amount"] or 0) for row in rows if row["entry_type"] == "Income")
        expenses = sum(float(row["amount"] or 0) for row in rows if row["entry_type"] == "Expense")
        return {"income": income, "expenses": expenses, "balance": income - expenses}
