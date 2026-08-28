import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from daao.gui import CameraCompassWidget
except ImportError:
    QApplication = None
    CameraCompassWidget = None


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class GuiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_widget_accepts_compass_state(self) -> None:
        widget = CameraCompassWidget()
        widget.resize(800, 450)
        widget.set_heading(359.5, 2.0)
        widget.set_attitude(15.0, -12.0)
        widget.horizontal_fov = 74.0
        widget.show()
        self.app.processEvents()
        self.assertEqual(widget.heading, 359.5)
        self.assertEqual(widget.heading_accuracy, 2.0)
        self.assertEqual(widget.camera_elevation, 15.0)
        self.assertEqual(widget.camera_roll, -12.0)
        self.assertFalse(widget.grab().toImage().isNull())
        widget.close()


if __name__ == "__main__":
    unittest.main()
