import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from personal_app.app import AppContext
from personal_app.gui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Momentum")
    app.setOrganizationName("PersonalCommandCentre")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "assets" / "darg_app_icon.ico")))

    context = AppContext.create()
    window = MainWindow(context)
    window.show()

    return app.exec()
