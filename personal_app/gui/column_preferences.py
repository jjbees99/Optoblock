import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMenu, QTableWidget


DEFAULT_VISIBLE = {
    "Tasks": [0, 1], "Projects": [1], "Shopping": [0, 1],
    "Bills & Renewals": [0], "Documents": [0],
    "Errands & Appointments": [0, 1], "Follow-Up": [0],
    "Travel & Plans": [0], "Home / Flat / Living": [0],
    "Finance": [0, 3, 4], "Unwind": [0, 1],
}


class ColumnPreferences:
    """Progressive disclosure for existing database fields, stored per module."""

    def __init__(self, table: QTableWidget, settings, module: str, headers: list[str]) -> None:
        self.table, self.settings, self.module, self.headers = table, settings, module, headers
        self.key = f"columns:{module}"
        table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        header = table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._menu)
        self.restore()
        header.sectionMoved.connect(lambda *_: self.save())
        header.sectionResized.connect(lambda *_: self.save())

    def _state(self) -> dict:
        try:
            return json.loads(self.settings.get(self.key, "") or "")
        except (TypeError, ValueError):
            return {}

    def restore(self) -> None:
        state = self._state()
        visible = set(state.get("visible", DEFAULT_VISIBLE.get(self.module, [0])))
        aliases = state.get("aliases", {})
        self.table.setHorizontalHeaderLabels([aliases.get(str(i), name) for i, name in enumerate(self.headers)])
        for col in range(len(self.headers)):
            self.table.setColumnHidden(col, col not in visible)
            width = state.get("widths", {}).get(str(col))
            if width: self.table.setColumnWidth(col, int(width))
        order = state.get("order", [])
        header = self.table.horizontalHeader()
        for visual, logical in enumerate(order):
            current = header.visualIndex(int(logical))
            if current >= 0 and current != visual: header.moveSection(current, visual)
        self._fit_primary()

    def _fit_primary(self) -> None:
        visible = [i for i in range(len(self.headers)) if not self.table.isColumnHidden(i)]
        if len(visible) == 1:
            self.table.horizontalHeader().setStretchLastSection(True)

    def save(self) -> None:
        header = self.table.horizontalHeader()
        prior = self._state()
        state = {
            "visible": [i for i in range(len(self.headers)) if not self.table.isColumnHidden(i)],
            "widths": {str(i): self.table.columnWidth(i) for i in range(len(self.headers))},
            "order": [header.logicalIndex(i) for i in range(header.count())],
            "aliases": prior.get("aliases", {}),
        }
        self.settings.set(self.key, json.dumps(state))

    def _menu(self, point) -> None:
        menu = QMenu(self.table)
        add = menu.addMenu("Add field")
        for col, name in enumerate(self.headers):
            action = add.addAction(name)
            action.setCheckable(True); action.setChecked(not self.table.isColumnHidden(col))
            action.triggered.connect(lambda checked, c=col: self._set_visible(c, checked))
        current = self.table.horizontalHeader().logicalIndexAt(point)
        if current >= 0:
            menu.addSeparator()
            rename = menu.addAction("Rename field…")
            rename.triggered.connect(lambda: self._rename(current))
            if current not in DEFAULT_VISIBLE.get(self.module, [0]):
                hide = menu.addAction("Hide field")
                hide.triggered.connect(lambda: self._set_visible(current, False))
        menu.exec(self.table.horizontalHeader().mapToGlobal(point))

    def _set_visible(self, col: int, visible: bool) -> None:
        self.table.setColumnHidden(col, not visible); self._fit_primary(); self.save()

    def _rename(self, col: int) -> None:
        current = self.table.horizontalHeaderItem(col).text()
        text, ok = QInputDialog.getText(self.table, "Rename field", "Field name", text=current)
        if ok and text.strip():
            state = self._state(); state.setdefault("aliases", {})[str(col)] = text.strip()
            self.settings.set(self.key, json.dumps(state)); self.restore()


def configure_columns(table, context, module, headers):
    table.column_preferences = ColumnPreferences(table, context.settings, module, headers)
    return table.column_preferences
