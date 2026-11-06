import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from personal_app.app import AppContext
from personal_app.gui.main_window import MainWindow
from personal_app.remote.server import LOG, PhoneServer, configure_file_logging


def run() -> int:
    configure_file_logging()
    LOG.info("Optoblock started")
    app = QApplication(sys.argv)
    app.setApplicationName("Optoblock")
    app.setOrganizationName("Optoblock")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "assets" / "darg_app_icon.ico")))

    context = AppContext.create()
    phone_server = None
    if context.settings.get("phone_access_enabled", "true") == "true":
        try:
            phone_server = PhoneServer(context.service)
            phone_server.start()
        except BaseException as exc:
            # Phone access is optional and must never prevent the desktop UI.
            LOG.exception("Phone server startup failed")
            if phone_server is not None:
                phone_server.error = f"Phone server failed: {exc}"
    context.phone_server_status = ("Running" if phone_server and not phone_server.error else
                                   phone_server.error if phone_server else "Disabled")
    window = MainWindow(context)
    window.phone_server = phone_server
    window.show()

    return app.exec()
