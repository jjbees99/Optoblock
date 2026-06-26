from personal_app.data.database import Database


DEFAULTS = {
    "theme": "Dark",
    "startup_modules": "Dashboard,Tasks,Projects,Finance",
    "backup_location": "",
    "daily_focus": "",
    "accent_color": "#63d4c7",
    "table_color": "#1f2a2e",
    "compact_mode": "Comfortable",
}


class SettingsManager:
    def __init__(self, db: Database) -> None:
        self.db = db
        for key, value in DEFAULTS.items():
            if self.get(key, None) is None:
                self.set(key, value)
        if self.get("theme") == "Warm Light":
            self.set("theme", "Dark")
        modules = self.startup_modules()
        if "Finance" not in modules:
            modules.insert(min(3, len(modules)), "Finance")
            self.set_startup_modules(modules)

    def get(self, key: str, default: str | None = "") -> str | None:
        row = self.db.one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    def startup_modules(self) -> list[str]:
        return [part.strip() for part in (self.get("startup_modules") or "").split(",") if part.strip()]

    def set_startup_modules(self, modules: list[str]) -> None:
        self.set("startup_modules", ",".join(modules))
