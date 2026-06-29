from __future__ import annotations

from personal_app.data.models import DashboardModule


GRID_COLUMNS = 3
GRID_ROWS = 3
ALLOWED_SIZES = {(1, 1), (1, 2), (2, 1), (2, 2)}


class DashboardLayout:
    def __init__(self, modules: list[DashboardModule] | None = None) -> None:
        self.modules = modules or []

    def module(self, module_id: str) -> DashboardModule | None:
        return next((module for module in self.modules if module.id == module_id), None)

    def can_place(
        self,
        module_id: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> bool:
        if (width, height) not in ALLOWED_SIZES:
            return False
        if x < 0 or y < 0 or x + width > GRID_COLUMNS or y + height > GRID_ROWS:
            return False
        requested = self._cells(x, y, width, height)
        for module in self.modules:
            if module.id == module_id:
                continue
            if requested & self._cells(module.x, module.y, module.width, module.height):
                return False
        return True

    def place(self, module_id: str, x: int, y: int, width: int, height: int) -> bool:
        module = self.module(module_id)
        if not module or not self.can_place(module_id, x, y, width, height):
            return False
        module.x = x
        module.y = y
        module.width = width
        module.height = height
        return True

    def first_available(self, width: int = 1, height: int = 1, module_id: str = "") -> tuple[int, int] | None:
        for y in range(GRID_ROWS):
            for x in range(GRID_COLUMNS):
                if self.can_place(module_id, x, y, width, height):
                    return x, y
        return None

    def add(self, module: DashboardModule) -> bool:
        if self.module(module.id) or not self.can_place(module.id, module.x, module.y, module.width, module.height):
            return False
        self.modules.append(module)
        return True

    def remove(self, module_id: str) -> None:
        self.modules = [module for module in self.modules if module.id != module_id]

    def is_valid(self) -> bool:
        return all(
            self.can_place(module.id, module.x, module.y, module.width, module.height)
            for module in self.modules
        )

    @staticmethod
    def _cells(x: int, y: int, width: int, height: int) -> set[tuple[int, int]]:
        return {(cell_x, cell_y) for cell_y in range(y, y + height) for cell_x in range(x, x + width)}
