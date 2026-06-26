from PySide6.QtWidgets import QFileDialog, QComboBox, QFormLayout, QLabel, QLineEdit, QPushButton

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment


class SettingsPage(Compartment):
    def __init__(self, context: AppContext, theme_changed=None) -> None:
        super().__init__("Settings", "Theme, colours, backups, imports, exports, and workspace feel.", "Settings")
        self.context = context
        self.theme_changed = theme_changed
        form = QFormLayout()
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Warm Light"])
        self.theme.setCurrentText(context.settings.get("theme") or "Dark")
        self.theme.currentTextChanged.connect(self.save)
        self.accent = QLineEdit(context.settings.get("accent_color") or "#63d4c7")
        self.table_color = QLineEdit(context.settings.get("table_color") or "#1f2a2e")
        self.density = QComboBox()
        self.density.addItems(["Comfortable", "Compact"])
        self.density.setCurrentText(context.settings.get("compact_mode") or "Comfortable")
        self.accent.textChanged.connect(self.save)
        self.table_color.textChanged.connect(self.save)
        self.density.currentTextChanged.connect(self.save)
        self.backup = QLineEdit(context.settings.get("backup_location") or "")
        self.backup.textChanged.connect(self.save)
        form.addRow("Theme", self.theme)
        form.addRow("Accent colour", self.accent)
        form.addRow("Table colour", self.table_color)
        form.addRow("Density", self.density)
        form.addRow("Backup location", self.backup)
        export_btn = QPushButton("Export JSON")
        import_btn = QPushButton("Import JSON")
        export_btn.clicked.connect(self.export_json)
        import_btn.clicked.connect(self.import_json)
        self.notice = QLabel()
        self.layout.addLayout(form)
        self.layout.addWidget(export_btn)
        self.layout.addWidget(import_btn)
        self.layout.addWidget(self.notice)

    def save(self) -> None:
        self.context.settings.set("theme", self.theme.currentText())
        self.context.settings.set("accent_color", self.accent.text().strip() or "#63d4c7")
        self.context.settings.set("table_color", self.table_color.text().strip() or "#1f2a2e")
        self.context.settings.set("compact_mode", self.density.currentText())
        self.context.settings.set("backup_location", self.backup.text())
        if self.theme_changed:
            self.theme_changed()

    def export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Optoblock data", self.backup.text() or "optoblock-backup.json", "JSON (*.json)")
        if path:
            self.context.storage.export_json(path)
            self.backup.setText(path)
            self.notice.setText("Export complete.")

    def import_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Optoblock data", self.backup.text(), "JSON (*.json)")
        if path:
            self.context.storage.import_json(path)
            self.notice.setText("Import complete. Restart or refresh modules to see all changes.")
