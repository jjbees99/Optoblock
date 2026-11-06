from datetime import datetime

from PySide6.QtCore import QMimeData, Qt, Signal, QTimer
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment, subtle_button
from personal_app.gui.column_preferences import configure_columns
from personal_app.gui.drag_payloads import TASK_MIME_TYPE, encode_task


TASK_COLUMNS = ["Done", "Name", "Description", "Category", "Due Date", "Priority", "Status"]
CATEGORY_COLUMN = TASK_COLUMNS.index("Category")


class AlphabeticalItem(QTableWidgetItem):
    def __lt__(self, other):
        return self.text().casefold() < other.text().casefold()


class DraggableTaskTable(QTableWidget):
    """Exports a task title while retaining the normal editable table behaviour."""

    def mimeData(self, items):
        mime = QMimeData()
        rows = {item.row() for item in items}
        row = next(iter(rows), self.currentRow())
        title_item = self.item(row, 1) if row >= 0 else None
        title = title_item.text().strip() if title_item else ""
        if title:
            mime.setData(TASK_MIME_TYPE, encode_task(title))
            mime.setText(title)
        return mime


class TasksPage(Compartment):
    archive_changed = Signal()

    def __init__(self, context: AppContext) -> None:
        super().__init__("To-Do List", "Spreadsheet-style task planning: edit cells, choose priority/status, then save.", "Tasks")
        self.context = context
        self._loading = False
        self._remote_refresh_pending = False
        self._save_timer = QTimer(self); self._save_timer.setSingleShot(True); self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self.save)
        self.table = DraggableTaskTable(0, len(TASK_COLUMNS))
        self.table.setHorizontalHeaderLabels(TASK_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setDragEnabled(True)
        self.table.setDragDropMode(QAbstractItemView.DragOnly)
        self.table.setDefaultDropAction(Qt.CopyAction)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._schedule_save)
        self.table.horizontalHeader().sectionClicked.connect(self._sort_by_column)
        configure_columns(self.table, context, "Tasks", TASK_COLUMNS)
        controls = QHBoxLayout()
        add = QPushButton("Add new")
        self.filter = QComboBox()
        self.filter.addItems(["All", "Active", "Completed", "High priority", "Due soon"])
        self.filter.currentTextChanged.connect(self.refresh)
        archive_selected = subtle_button("Archive selected")
        archive_done = subtle_button("Archive done")
        remove = subtle_button("Remove")
        add.clicked.connect(self.add_row)
        archive_selected.clicked.connect(self.archive_selected)
        archive_done.clicked.connect(self.archive_completed)
        remove.clicked.connect(self.delete_row)
        controls.addWidget(self.filter)
        for button in (add, archive_selected, archive_done, remove):
            controls.addWidget(button)
        controls.addStretch(1)
        self.notice = QLabel()
        self.notice.setObjectName("InlineNotice")
        self.layout.addWidget(self.table, 1)
        self.layout.addLayout(controls)
        self.layout.addWidget(self.notice)
        self.refresh()

    def refresh(self, *_args) -> None:
        self._save_timer.stop(); self._loading = True
        self.table.setRowCount(0)
        filter_name = self.filter.currentText() if hasattr(self, "filter") else "All"
        for row in self.context.tasks.list(filter_name):
            if row["status"] == "Archived":
                continue
            self.add_row(
                [
                    row["status"] == "Completed",
                    row["name"],
                    row["description"],
                    row["category"],
                    row["due_date"],
                    row["priority"],
                    row["status"],
                    row["id"],
                ]
            )
        self._loading = False

    def request_remote_refresh(self) -> None:
        """Do not destroy a desktop selection or active cell editor for a phone update."""
        if self._save_timer.isActive() or self.table.state() == QAbstractItemView.EditingState or self.table.selectionModel().hasSelection():
            self._remote_refresh_pending = True
            self.notice.setText("Phone changes received; this view will update after the current action.")
            return
        self.refresh()

    def _finish_action(self) -> None:
        self.refresh()
        self._remote_refresh_pending = False

    def add_row(self, values: list | None = None) -> None:
        values = values or [False, "", "", "", "", "Medium", "Active", None]
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        done = QTableWidgetItem("")
        done.setFlags(done.flags() | Qt.ItemIsUserCheckable)
        done.setCheckState(Qt.Checked if values[0] else Qt.Unchecked)
        done.setData(Qt.UserRole, values[7] if len(values) > 7 else None)
        self.table.setItem(row_index, 0, done)

        for col, value in enumerate(values[1:5], start=1):
            item = AlphabeticalItem(str(value)) if col == CATEGORY_COLUMN else QTableWidgetItem(str(value))
            self.table.setItem(row_index, col, item)

        priority = QComboBox()
        priority.addItems(["Low", "Medium", "High"])
        priority.setCurrentText(values[5] or "Medium")
        priority.currentTextChanged.connect(self._schedule_save)
        self.table.setCellWidget(row_index, 5, priority)

        status = QComboBox()
        status.addItems(["Active", "Completed", "Archived"])
        status.setCurrentText(values[6] or "Active")
        status.currentTextChanged.connect(self._schedule_save)
        self.table.setCellWidget(row_index, 6, status)

    def save(self) -> None:
        if self._loading: return
        self._save_timer.stop()
        for row in range(self.table.rowCount()):
            name = self._cell(row, 1)
            if not name:
                continue
            done = self.table.item(row, 0).checkState() == Qt.Checked
            status = self._combo(row, 6)
            if done and status == "Active":
                status = "Completed"
            values = {
                    "name": name,
                    "description": self._cell(row, 2),
                    "category": self._cell(row, 3),
                    "due_date": self._cell(row, 4),
                    "priority": self._combo(row, 5),
                    "status": status,
                    "completed_at": datetime.now().isoformat(timespec="seconds") if status == "Completed" else "",
                }
            item_id = self.table.item(row, 0).data(Qt.UserRole)
            if item_id:
                self.context.tasks.update(int(item_id), values["name"], values["description"], values["category"], values["due_date"], values["priority"])
                self.context.db.execute("UPDATE tasks SET status=?, completed_at=? WHERE id=?", (values["status"], values["completed_at"], item_id))
            else:
                item_id = self.context.tasks.add(values["name"], values["description"], values["category"], values["due_date"], values["priority"])
                self.table.item(row, 0).setData(Qt.UserRole, item_id)
                if values["status"] != "Active": self.context.db.execute("UPDATE tasks SET status=?, completed_at=? WHERE id=?", (values["status"], values["completed_at"], item_id))

    def _schedule_save(self, *_args) -> None:
        if not self._loading: self._save_timer.start()

    def _sort_by_column(self, column: int) -> None:
        if column == CATEGORY_COLUMN:
            self.table.sortItems(CATEGORY_COLUMN, Qt.AscendingOrder)
            self.table.horizontalHeader().setSortIndicator(CATEGORY_COLUMN, Qt.AscendingOrder)
            self.table.horizontalHeader().setSortIndicatorShown(True)

    def archive_completed(self) -> None:
        self.save()
        self.context.tasks.archive_completed()
        self._finish_action()
        self.archive_changed.emit()

    def archive_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        if not rows:
            self.notice.setText("Select one or more tasks to archive.")
            return
        self.save()
        task_ids = [self.table.item(row, 0).data(Qt.UserRole) for row in rows]
        for task_id in task_ids:
            if task_id is not None:
                self.context.tasks.archive(int(task_id))
        archived_count = sum(task_id is not None for task_id in task_ids)
        self._finish_action()
        self.notice.setText(f"Archived {archived_count} task{'s' if archived_count != 1 else ''}.")
        self.archive_changed.emit()

    def delete_row(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self.notice.setText("Select a task to remove.")
            return
        item_id = self.table.item(row, 0).data(Qt.UserRole)
        if item_id: self.context.tasks.delete(int(item_id))
        self.table.removeRow(row)
        self.notice.setText("Task removed.")

    def _cell(self, row: int, col: int) -> str:
        item = self.table.item(row, col)
        return item.text().strip() if item else ""

    def _combo(self, row: int, col: int) -> str:
        widget = self.table.cellWidget(row, col)
        return widget.currentText() if isinstance(widget, QComboBox) else ""
