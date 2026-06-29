from PySide6.QtCore import QRect, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from personal_app.app import AppContext
from personal_app.data.models import DashboardModule
from personal_app.gui.module_registry import MODULE_OUTLINES, MODULE_TITLES, module_factory
from personal_app.gui.styles import DARK, LIGHT
from personal_app.logic.dashboard_layout import GRID_COLUMNS, GRID_ROWS, DashboardLayout
from personal_app.logic.dashboard_storage import DashboardStorage


MODULES = list(MODULE_TITLES)
FOCUS_LAYOUT = [
    ("Tasks", 0, 0, 1, 1),
    ("Shopping", 1, 0, 1, 1),
    ("Voice Brain Dump", 2, 0, 1, 2),
    ("Archive", 0, 1, 1, 1),
    ("Projects", 1, 1, 1, 1),
    ("Unwind", 0, 2, 1, 1),
    ("Focus Timer", 1, 2, 1, 1),
]
UNWINDING_LAYOUT = [
    ("Unwind", 0, 0, 2, 2),
    ("Recipes", 2, 0, 1, 2),
    ("Shopping", 0, 2, 1, 1),
    ("Brain Dump Scanner", 1, 2, 1, 1),
    ("Archive", 2, 2, 1, 1),
]
PROFILE_LAYOUTS = {"Focus Work": FOCUS_LAYOUT, "Unwinding": UNWINDING_LAYOUT}
GRID_MARGIN = 14
GRID_GAP = 10


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext) -> None:
        super().__init__()
        self.context = context
        self.storage = DashboardStorage()
        self.active_profile, self.profiles = self.storage.load_profiles()
        for profile_name in PROFILE_LAYOUTS:
            candidate = DashboardLayout(self.profiles.get(profile_name, []))
            if not candidate.modules or not candidate.is_valid():
                self.profiles[profile_name] = self._default_modules(profile_name)
        if self.active_profile not in self.profiles:
            self.active_profile = "Focus Work"
        self.dashboard = DashboardLayout(self.profiles[self.active_profile])
        self._persist_profiles()

        self.setWindowTitle("Optoblock")
        self.resize(1320, 860)
        self.module_checks: dict[str, QCheckBox] = {}
        self.widgets_by_module: dict[str, QWidget] = {}
        self.slot_frames: list[QFrame] = []

        self.root = QWidget()
        self.root.setObjectName("Root")
        self.setCentralWidget(self.root)
        self.outer = QVBoxLayout(self.root)
        self.outer.setContentsMargins(18, 14, 18, 18)
        self.outer.setSpacing(10)
        self._build_top_bar()

        self.table = QFrame()
        self.table.setObjectName("Table")
        self.table.setMinimumHeight(680)
        self.outer.addWidget(self.table, 1)
        self._build_slots()

        self.apply_theme()
        self.rebuild_table()

    def _build_top_bar(self) -> None:
        top = QHBoxLayout()
        app_name = QLabel("Optoblock")
        app_name.setObjectName("AppName")
        top.addWidget(app_name)
        self.notice = QLabel("Drag modules or their edges. Changes save to the selected loadout.")
        self.notice.setObjectName("WorkspaceNotice")
        top.addWidget(self.notice, 1)

        self.profile_picker = QComboBox()
        self.profile_picker.setObjectName("ProfilePicker")
        self.profile_picker.addItems(PROFILE_LAYOUTS)
        self.profile_picker.setCurrentText(self.active_profile)
        self.profile_picker.currentTextChanged.connect(self.switch_profile)
        top.addWidget(self.profile_picker)

        picker = QToolButton()
        picker.setText("Modules")
        picker.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(picker)
        active = {module.id for module in self.dashboard.modules}
        for module in MODULES:
            check = QCheckBox(MODULE_TITLES[module])
            check.setChecked(module in active)
            check.stateChanged.connect(lambda _state, name=module: self._module_changed(name))
            action = QWidgetAction(menu)
            action.setDefaultWidget(check)
            menu.addAction(action)
            self.module_checks[module] = check
        picker.setMenu(menu)
        top.addWidget(picker)
        self.outer.addLayout(top)

    def _build_slots(self) -> None:
        for _ in range(GRID_COLUMNS * GRID_ROWS):
            slot = QFrame(self.table)
            slot.setObjectName("GridSlot")
            slot.lower()
            slot.show()
            self.slot_frames.append(slot)

    def _module_changed(self, name: str) -> None:
        check = self.module_checks[name]
        if check.isChecked():
            location = self.dashboard.first_available(module_id=name)
            if location is None:
                check.blockSignals(True)
                check.setChecked(False)
                check.blockSignals(False)
                self._show_error("All 9 dashboard slots are occupied. Move, resize, or remove a module first.")
                return
            x, y = location
            self.dashboard.add(
                DashboardModule(
                    id=name,
                    title=MODULE_TITLES[name],
                    type=name,
                    x=x,
                    y=y,
                )
            )
        else:
            self.dashboard.remove(name)
        self._save_and_rebuild()

    def rebuild_table(self) -> None:
        for widget in list(self.widgets_by_module.values()):
            widget.deleteLater()
        self.widgets_by_module.clear()

        for module in self.dashboard.modules:
            widget = module_factory(self.context, module.type, self.apply_theme)()
            widget.module_name = module.id
            widget.set_grid_mode(True)
            widget.set_outline_colour(MODULE_OUTLINES.get(module.type, "#63d4c7"))
            widget.dropped.connect(self.move_module_at_drop)
            widget.geometry_changed.connect(self.resize_module_from_edges)
            if hasattr(widget, "items_added"):
                widget.items_added.connect(self.refresh_destination_modules)
            if hasattr(widget, "archive_changed"):
                widget.archive_changed.connect(lambda: self.refresh_module("Archive"))
            widget.setParent(self.table)
            widget.show()
            self.widgets_by_module[module.id] = widget
        QTimer.singleShot(0, self.position_grid_items)

    def refresh_destination_modules(self, counts: dict[str, int]) -> None:
        destinations = {
            "To-Do": "Tasks",
            "Reminder Candidate": "Tasks",
            "Shopping": "Shopping",
            "Projects / Learning": "Projects",
            "Archive / Notes": "Archive",
        }
        for category, module_name in destinations.items():
            if not counts.get(category):
                continue
            self.refresh_module(module_name)

    def refresh_module(self, module_name: str) -> None:
        widget = self.widgets_by_module.get(module_name)
        refresh = getattr(widget, "refresh", None)
        if callable(refresh):
            refresh()

    def move_module_at_drop(self, module_id: str, global_pos) -> None:
        module = self.dashboard.module(module_id)
        if not module:
            return
        local = self.table.mapFromGlobal(global_pos)
        cell_width, cell_height = self._cell_size()
        x = round((local.x() - GRID_MARGIN - cell_width / 2) / (cell_width + GRID_GAP))
        y = round((local.y() - GRID_MARGIN - cell_height / 2) / (cell_height + GRID_GAP))
        if not self.dashboard.place(module_id, x, y, module.width, module.height):
            self.position_grid_items()
            self._show_error("That position does not have enough free slots for this module.")
            return
        self._persist_profiles()
        self.position_grid_items()
        self._set_notice(f"{module.title} moved to row {y + 1}, column {x + 1}.")

    def resize_module_from_edges(self, module_id: str) -> None:
        module = self.dashboard.module(module_id)
        widget = self.widgets_by_module.get(module_id)
        if not module or not widget:
            return
        cell_width, cell_height = self._cell_size()
        x = round((widget.x() - GRID_MARGIN) / (cell_width + GRID_GAP))
        y = round((widget.y() - GRID_MARGIN) / (cell_height + GRID_GAP))
        width = max(1, min(2, round((widget.width() + GRID_GAP) / (cell_width + GRID_GAP))))
        height = max(1, min(2, round((widget.height() + GRID_GAP) / (cell_height + GRID_GAP))))
        if not self.dashboard.place(module_id, x, y, width, height):
            self.position_grid_items()
            self._show_error(f"{module.title} cannot fill those slots because they are occupied.")
            return
        self._persist_profiles()
        self.position_grid_items()
        self._set_notice(f"{module.title} resized to {width} x {height}.")

    def switch_profile(self, profile_name: str) -> None:
        if profile_name == self.active_profile or profile_name not in self.profiles:
            return
        self._persist_profiles()
        self.active_profile = profile_name
        self.dashboard = DashboardLayout(self.profiles[profile_name])
        self._sync_module_checks()
        self._persist_profiles()
        self.rebuild_table()
        self._set_notice(f"Loaded {profile_name} loadout.")

    def position_grid_items(self) -> None:
        for index, slot in enumerate(self.slot_frames):
            slot.setGeometry(self._grid_geometry(index % GRID_COLUMNS, index // GRID_COLUMNS, 1, 1))
            slot.lower()
        for module in self.dashboard.modules:
            widget = self.widgets_by_module.get(module.id)
            if widget:
                widget.setGeometry(self._grid_geometry(module.x, module.y, module.width, module.height))
                widget.raise_()

    def _grid_geometry(self, x: int, y: int, width: int, height: int) -> QRect:
        cell_width, cell_height = self._cell_size()
        left = GRID_MARGIN + x * (cell_width + GRID_GAP)
        top = GRID_MARGIN + y * (cell_height + GRID_GAP)
        pixel_width = width * cell_width + (width - 1) * GRID_GAP
        pixel_height = height * cell_height + (height - 1) * GRID_GAP
        return QRect(left, top, pixel_width, pixel_height)

    def _cell_size(self) -> tuple[int, int]:
        width = max(1, (self.table.width() - 2 * GRID_MARGIN - (GRID_COLUMNS - 1) * GRID_GAP) // GRID_COLUMNS)
        height = max(1, (self.table.height() - 2 * GRID_MARGIN - (GRID_ROWS - 1) * GRID_GAP) // GRID_ROWS)
        return width, height

    def _save_and_rebuild(self) -> None:
        self._persist_profiles()
        self.rebuild_table()

    def _persist_profiles(self) -> None:
        self.profiles[self.active_profile] = self.dashboard.modules
        self.storage.save_profiles(self.active_profile, self.profiles)

    def _sync_module_checks(self) -> None:
        active = {module.id for module in self.dashboard.modules}
        for name, check in self.module_checks.items():
            check.blockSignals(True)
            check.setChecked(name in active)
            check.blockSignals(False)

    def _show_error(self, message: str) -> None:
        self._set_notice(message)
        QMessageBox.information(self, "Dashboard layout", message)

    def _set_notice(self, message: str) -> None:
        self.notice.setText(message)

    def _default_modules(self, profile_name: str = "Focus Work") -> list[DashboardModule]:
        return [
            DashboardModule(
                id=name,
                title=MODULE_TITLES[name],
                type=name,
                x=x,
                y=y,
                width=width,
                height=height,
            )
            for name, x, y, width, height in PROFILE_LAYOUTS[profile_name]
        ]

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.position_grid_items()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.position_grid_items()

    def apply_theme(self) -> None:
        theme = self.context.settings.get("theme") or "Dark"
        stylesheet = DARK if theme == "Dark" else LIGHT
        accent = self.context.settings.get("accent_color") or "#63d4c7"
        table = self.context.settings.get("table_color") or "#1f2a2e"
        stylesheet = stylesheet.replace("__ACCENT__", accent).replace("__TABLE__", table)
        self.setStyleSheet(stylesheet)

    def refresh_appearance(self) -> None:
        self.apply_theme()
        self.rebuild_table()
