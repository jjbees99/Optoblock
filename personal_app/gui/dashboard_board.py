from __future__ import annotations

from PySide6.QtCore import QRect, QTimer
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QMenu, QMessageBox, QToolButton, QVBoxLayout, QWidget, QWidgetAction

from personal_app.app import AppContext
from personal_app.data.models import DashboardModule
from personal_app.gui.module_registry import MODULE_TITLES, module_factory
from personal_app.logic.dashboard_layout import DashboardLayout
from personal_app.logic.dashboard_storage import DashboardStorage


COLUMNS, ROWS = 4, 3
MARGIN, GAP = 10, 10
BOARD_MODULES = [
    "Dashboard", "Tasks", "Projects", "Shopping", "Brain Dump Scanner",
    "Bills & Renewals", "Documents", "Errands & Appointments", "Follow-Up",
    "Travel & Plans", "Home / Flat / Living", "Archive", "Finance", "Unwind",
]
DEFAULT_LAYOUT = [
    ("Tasks", 0, 0, 2, 2), ("Dashboard", 2, 0, 2, 1),
    ("Bills & Renewals", 2, 1, 1, 1), ("Follow-Up", 3, 1, 1, 1),
    ("Shopping", 0, 2, 1, 1), ("Brain Dump Scanner", 1, 2, 1, 1),
    ("Projects", 2, 2, 1, 1), ("Errands & Appointments", 3, 2, 1, 1),
]


class DashboardBoard(QWidget):
    """A saved 4×3 module canvas living alongside the focused sidebar pages."""

    def __init__(self, context: AppContext, destination_changed=None) -> None:
        super().__init__()
        self.context = context
        self.destination_changed = destination_changed
        self.storage = DashboardStorage()
        active, profiles = self.storage.load_profiles()
        saved = profiles.get("Workspace 4x3") or []
        candidate = DashboardLayout(saved, COLUMNS, ROWS)
        self.dashboard = candidate if saved and candidate.is_valid() else DashboardLayout(self._defaults(), COLUMNS, ROWS)
        self.widgets_by_module: dict[str, QWidget] = {}
        self.module_checks: dict[str, QCheckBox] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("BoardTitle")
        description = QLabel("Drag modules around your 4 × 3 workspace. Resize from any card edge.")
        description.setObjectName("BoardDescription")
        titles.addWidget(title)
        titles.addWidget(description)
        header.addLayout(titles)
        header.addStretch(1)
        picker = QToolButton()
        picker.setText("Customize")
        picker.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(picker)
        active_ids = {module.id for module in self.dashboard.modules}
        for module in BOARD_MODULES:
            check = QCheckBox(MODULE_TITLES[module])
            check.setChecked(module in active_ids)
            check.stateChanged.connect(lambda _state, name=module: self._module_changed(name))
            action = QWidgetAction(menu)
            action.setDefaultWidget(check)
            menu.addAction(action)
            self.module_checks[module] = check
        picker.setMenu(menu)
        header.addWidget(picker)
        outer.addLayout(header)

        self.canvas = QFrame()
        self.canvas.setObjectName("DashboardCanvas")
        self.canvas.setMinimumHeight(560)
        outer.addWidget(self.canvas, 1)
        self.slots = []
        for _ in range(COLUMNS * ROWS):
            slot = QFrame(self.canvas)
            slot.setObjectName("DashboardSlot")
            slot.lower()
            self.slots.append(slot)
        self.rebuild()

    def _defaults(self) -> list[DashboardModule]:
        return [DashboardModule(name, MODULE_TITLES[name], name, x, y, w, h) for name, x, y, w, h in DEFAULT_LAYOUT]

    def rebuild(self) -> None:
        self._save_project()
        for widget in self.widgets_by_module.values():
            widget.deleteLater()
        self.widgets_by_module.clear()
        for module in self.dashboard.modules:
            widget = module_factory(self.context, module.type)()
            widget.module_name = module.id
            widget.set_grid_mode(True)
            widget.dropped.connect(self.move_module_at_drop)
            widget.geometry_changed.connect(self.resize_module_from_edges)
            if hasattr(widget, "items_added") and self.destination_changed:
                widget.items_added.connect(self.destination_changed)
            widget.setParent(self.canvas)
            widget.show()
            self.widgets_by_module[module.id] = widget
        self._persist()
        QTimer.singleShot(0, self.position_items)

    def _module_changed(self, name: str) -> None:
        check = self.module_checks[name]
        if check.isChecked():
            location = self.dashboard.first_available(module_id=name)
            if location is None:
                check.blockSignals(True); check.setChecked(False); check.blockSignals(False)
                QMessageBox.information(self, "Dashboard", "The 4 × 3 board is full. Remove or resize a module first.")
                return
            self.dashboard.add(DashboardModule(name, MODULE_TITLES[name], name, *location))
        else:
            self.dashboard.remove(name)
        self.rebuild()

    def move_module_at_drop(self, module_id: str, global_pos) -> None:
        module = self.dashboard.module(module_id)
        if not module:
            return
        local = self.canvas.mapFromGlobal(global_pos)
        cw, ch = self._cell_size()
        x = round((local.x() - MARGIN - cw / 2) / (cw + GAP))
        y = round((local.y() - MARGIN - ch / 2) / (ch + GAP))
        if not self.dashboard.place(module_id, x, y, module.width, module.height):
            self.position_items()
            return
        self._persist(); self.position_items()

    def resize_module_from_edges(self, module_id: str) -> None:
        module, widget = self.dashboard.module(module_id), self.widgets_by_module.get(module_id)
        if not module or not widget:
            return
        cw, ch = self._cell_size()
        x = round((widget.x() - MARGIN) / (cw + GAP)); y = round((widget.y() - MARGIN) / (ch + GAP))
        width = max(1, min(2, round((widget.width() + GAP) / (cw + GAP))))
        height = max(1, min(2, round((widget.height() + GAP) / (ch + GAP))))
        if not self.dashboard.place(module_id, x, y, width, height):
            self.position_items(); return
        self._persist(); self.position_items()

    def position_items(self) -> None:
        for index, slot in enumerate(self.slots):
            slot.setGeometry(self._geometry(index % COLUMNS, index // COLUMNS, 1, 1)); slot.lower()
        for module in self.dashboard.modules:
            widget = self.widgets_by_module.get(module.id)
            if widget:
                widget.setGeometry(self._geometry(module.x, module.y, module.width, module.height)); widget.raise_()

    def _geometry(self, x: int, y: int, width: int, height: int) -> QRect:
        cw, ch = self._cell_size()
        return QRect(MARGIN + x * (cw + GAP), MARGIN + y * (ch + GAP), width * cw + (width - 1) * GAP, height * ch + (height - 1) * GAP)

    def _cell_size(self) -> tuple[int, int]:
        return (max(1, (self.canvas.width() - 2 * MARGIN - 3 * GAP) // COLUMNS), max(1, (self.canvas.height() - 2 * MARGIN - 2 * GAP) // ROWS))

    def _persist(self) -> None:
        active, profiles = self.storage.load_profiles()
        profiles["Workspace 4x3"] = self.dashboard.modules
        self.storage.save_profiles(active, profiles)

    def _save_project(self) -> None:
        widget = self.widgets_by_module.get("Projects")
        save = getattr(widget, "save_without_refresh", None)
        if callable(save): save()

    def refresh(self) -> None:
        for widget in self.widgets_by_module.values():
            refresh = getattr(widget, "refresh", None)
            if callable(refresh): refresh()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event); self.position_items()
