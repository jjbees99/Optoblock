import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable


LEGACY_APP_DIR = Path.home() / ("." + "momen" + "tum")
LEGACY_DB_PATH = LEGACY_APP_DIR / ("momen" + "tum.sqlite3")
APP_DIR = Path.home() / ".optoblock"
DB_PATH = APP_DIR / "optoblock.sqlite3"


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path == DB_PATH and not self.path.exists() and LEGACY_DB_PATH.exists():
            self.path.write_bytes(LEGACY_DB_PATH.read_bytes())

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    due_date TEXT DEFAULT '',
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'Active',
                    completed_at TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    status TEXT DEFAULT 'Idea',
                    next_action TEXT DEFAULT '',
                    next_action_done INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    category TEXT DEFAULT '',
                    bought INTEGER DEFAULT 0,
                    list_type TEXT DEFAULT 'Grocery',
                    archived INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    ingredients TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS unwind_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    activity_type TEXT DEFAULT 'recovery',
                    estimated_time TEXT DEFAULT '15 min',
                    done_today INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS brain_dump (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    body TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    archived INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS finance_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT DEFAULT '',
                    entry_type TEXT DEFAULT 'Expense',
                    category TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    amount REAL DEFAULT 0,
                    account TEXT DEFAULT '',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def all(self, query: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(query, tuple(params)).fetchall()]

    def one(self, query: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        rows = self.all(query, params)
        return rows[0] if rows else None

    def execute(self, query: str, params: Iterable[Any] = ()) -> int:
        with self.connect() as conn:
            cur = conn.execute(query, tuple(params))
            conn.commit()
            return int(cur.lastrowid)

    def execute_many(self, query: str, rows: Iterable[Iterable[Any]]) -> None:
        with self.connect() as conn:
            conn.executemany(query, rows)
            conn.commit()

    def export_json(self, target: Path) -> None:
        tables = ["tasks", "projects", "shopping_items", "recipes", "unwind_items", "settings", "brain_dump", "finance_entries"]
        payload = {table: self.all(f"SELECT * FROM {table}") for table in tables}
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def import_json(self, source: Path) -> None:
        payload = json.loads(source.read_text(encoding="utf-8"))
        with self.connect() as conn:
            for table, rows in payload.items():
                if not rows:
                    continue
                conn.execute(f"DELETE FROM {table}")
                columns = list(rows[0].keys())
                placeholders = ", ".join("?" for _ in columns)
                col_sql = ", ".join(columns)
                values = [tuple(row.get(col) for col in columns) for row in rows]
                conn.executemany(f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})", values)
            conn.commit()
