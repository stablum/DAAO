from __future__ import annotations

from importlib.metadata import version
import logging
import socket
import sys

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMessageBox

from daao.gui import MainWindow
from daao.logging_config import configure_logging
from daao.server import SensorServer


logger = logging.getLogger(__name__)


class UpdateBridge(QObject):
    """Moves receiver updates safely onto Qt's GUI thread."""

    update_received = Signal(object)


def local_ipv4_address() -> str:
    """Return the most useful local IPv4 address available."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 80))
        return str(probe.getsockname()[0])
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"
    finally:
        probe.close()


def main() -> int:
    log_path = configure_logging()
    logger.info("Starting DAAO version=%s log=%s", version("daao"), log_path)

    app = QApplication(sys.argv)
    app.setApplicationName("DIY Astronomical Attic Observatory")
    app.setOrganizationName("DAAO")

    bridge = UpdateBridge()
    server = SensorServer(host="0.0.0.0", port=8000, on_update=bridge.update_received.emit)
    try:
        server.start()
    except OSError as error:
        logger.exception("Could not listen on port 8000")
        QMessageBox.critical(
            None,
            "DAAO could not start",
            f"Could not listen on port 8000.\n\n{error}",
        )
        return 1

    push_url = f"http://{local_ipv4_address()}:{server.port}/data"
    logger.info("Sensor Logger push URL: %s", push_url)
    window = MainWindow(push_url=push_url)
    bridge.update_received.connect(window.apply_sensor_update)
    app.aboutToQuit.connect(server.stop)
    window.show()
    exit_code = app.exec()
    logger.info("DAAO stopped exit_code=%d", exit_code)
    return exit_code
