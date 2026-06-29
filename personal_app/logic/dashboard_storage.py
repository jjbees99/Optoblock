import json
from pathlib import Path

from personal_app.data.database import APP_DIR
from personal_app.data.models import DashboardModule


DEFAULT_LAYOUT_PATH = APP_DIR / "dashboard_layout.json"


class DashboardStorage:
    def __init__(self, path: Path = DEFAULT_LAYOUT_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[DashboardModule]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            rows = payload.get("modules", payload) if isinstance(payload, dict) else payload
            return [DashboardModule.from_dict(row) for row in rows if isinstance(row, dict)]
        except (OSError, ValueError, KeyError, TypeError):
            return []

    def save(self, modules: list[DashboardModule]) -> None:
        payload = {"version": 1, "modules": [module.to_dict() for module in modules]}
        self._write(payload)

    def load_profiles(self) -> tuple[str, dict[str, list[DashboardModule]]]:
        if not self.path.exists():
            return "Focus Work", {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and isinstance(payload.get("profiles"), dict):
                profiles = {
                    name: [DashboardModule.from_dict(row) for row in rows if isinstance(row, dict)]
                    for name, rows in payload["profiles"].items()
                    if isinstance(rows, list)
                }
                return str(payload.get("active_profile") or "Focus Work"), profiles
            legacy = self.load()
            return "Focus Work", {"Focus Work": legacy} if legacy else {}
        except (OSError, ValueError, KeyError, TypeError):
            return "Focus Work", {}

    def save_profiles(self, active_profile: str, profiles: dict[str, list[DashboardModule]]) -> None:
        payload = {
            "version": 2,
            "active_profile": active_profile,
            "profiles": {
                name: [module.to_dict() for module in modules]
                for name, modules in profiles.items()
            },
        }
        self._write(payload)

    def _write(self, payload: dict) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.path)
