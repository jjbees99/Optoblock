from __future__ import annotations

from PySide6.QtCore import QRect, QTimer
from PySide6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel, QMenu, QMessageBox, QToolButton, QVBoxLayout, QWidget, QWidgetAction

from personal_app.app import AppContext
from personal_app.data.models import DashboardModule
from personal_app.gui.module_registry import MODULE_TITLES, module_factory
from personal_app.logic.dashboard_layout import DashboardLayout
from personal_app.logic.dashboard_storage import DashboardStorage


COLUMNS, ROWS = 4, 3
MARGIN, GAP = 10, 10
BOARD_MODULES = [
    "Dashboard", "Day Planner", "Tasks", "Projects", "Shopping", "Brain Dump Scanner",
    "Bills & Renewals", "Documents", "Errands & Appointments", "Follow-Up",
    "Travel & Plans", "Home / Flat / Living", "Journal", "Notes", "Archive", "Finance",
    "Recipes", "Focus Timer", "Voice Brain Dump", "Unwind",
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
        active, self.profiles = self.storage.load_profiles()
        if not self.profiles:
            self.profiles = {"My Dashboard": self._defaults()}
            active = "My Dashboard"
        self.active_profile = active if active in self.profiles else next(iter(self.profiles))
        self.dashboard = self._profile_layout(self.active_profile)
        self.widgets_by_module: dict[str, QWidget] = {}
        self.module_checks: dict[str, QCheckBox] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("BoardTitle")
        titles.addWidget(title)
        header.addLayout(titles)
        header.addStretch(1)
        self.profile_picker = QComboBox()
        self.profile_picker.setToolTip("Choose a dashboard")
        self.profile_picker.setMinimumWidth(170)
        self._refresh_profile_picker()
        self.profile_picker.currentTextChanged.connect(self._switch_profile)
        header.addWidget(self.profile_picker)

        dashboard_actions = QToolButton()
        dashboard_actions.setText("Dashboards")
        dashboard_actions.setPopupMode(QToolButton.InstantPopup)
        dashboard_menu = QMenu(dashboard_actions)
        dashboard_menu.addAction("New dashboard…", self._new_profile)
        dashboard_menu.addAction("Rename dashboard…", self._rename_profile)
        dashboard_menu.addAction("Delete dashboard…", self._delete_profile)
        dashboard_actions.setMenu(dashboard_menu)
        header.addWidget(dashboard_actions)

        picker = QToolButton()
        picker.setText("Modules")
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

    @staticmethod
    def _copy_modules(modules: list[DashboardModule]) -> list[DashboardModule]:
        return [DashboardModule.from_dict(module.to_dict()) for module in modules]

    def _profile_layout(self, name: str) -> DashboardLayout:
        saved = [module for module in self._copy_modules(self.profiles.get(name, [])) if module.type in MODULE_TITLES]
        candidate = DashboardLayout(saved, COLUMNS, ROWS)
        return candidate if candidate.is_valid() else DashboardLayout(self._defaults(), COLUMNS, ROWS)

    def _refresh_profile_picker(self) -> None:
        self.profile_picker.blockSignals(True)
        self.profile_picker.clear()
        self.profile_picker.addItems(self.profiles.keys())
        self.profile_picker.setCurrentText(self.active_profile)
        self.profile_picker.blockSignals(False)

    def _sync_module_checks(self) -> None:
        active_ids = {module.id for module in self.dashboard.modules}
        for name, check in self.module_checks.items():
            check.blockSignals(True)
            check.setChecked(name in active_ids)
            check.blockSignals(False)

    def _switch_profile(self, name: str) -> None:
        if not name or name == self.active_profile or name not in self.profiles:
            return
        self._save_project()
        self._persist()
        self.active_profile = name
        self.dashboard = self._profile_layout(name)
        self._sync_module_checks()
        self.rebuild()

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "New dashboard", "Dashboard name")
        name = name.strip()
        if not ok or not name:
            return
        if any(existing.casefold() == name.casefold() for existing in self.profiles):
            QMessageBox.information(self, "Dashboards", "A dashboard with that name already exists.")
            return
        self._persist()
        self.profiles[name] = self._copy_modules(self.dashboard.modules)
        self.active_profile = name
        self.dashboard = self._profile_layout(name)
        self._refresh_profile_picker()
        self._sync_module_checks()
        self.rebuild()

    def _rename_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Rename dashboard", "Dashboard name", text=self.active_profile)
        name = name.strip()
        if not ok or not name or name == self.active_profile:
            return
        if any(existing.casefold() == name.casefold() for existing in self.profiles):
            QMessageBox.information(self, "Dashboards", "A dashboard with that name already exists.")
            return
        self._persist()
        renamed = {}
        for existing, modules in self.profiles.items():
            renamed[name if existing == self.active_profile else existing] = modules
        self.profiles = renamed
        self.active_profile = name
        self._refresh_profile_picker()
        self._persist()

    def _delete_profile(self) -> None:
        if len(self.profiles) == 1:
            QMessageBox.information(self, "Dashboards", "Keep at least one dashboard.")
            return
        if QMessageBox.question(self, "Delete dashboard", f'Delete "{self.active_profile}"?') != QMessageBox.Yes:
            return
        del self.profiles[self.active_profile]
        self.active_profile = next(iter(self.profiles))
        self.dashboard = self._profile_layout(self.active_profile)
        self._refresh_profile_picker()
        self._sync_module_checks()
        self.rebuild()

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
        self.profiles[self.active_profile] = self._copy_modules(self.dashboard.modules)
        self.storage.save_profiles(self.active_profile, self.profiles)

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
