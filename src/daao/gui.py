from __future__ import annotations

from datetime import datetime
import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Slot
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStatusBar,
)

from daao import __version__
from daao.compass import compass_marks, focal_length_pixels, project_delta_to_x
from daao.models import SensorUpdate


def overlay_font(point_size: int, weight: QFont.Weight) -> QFont:
    """Resolve a platform monospace font without assuming a family is installed."""
    font = QFont()
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSize(point_size)
    font.setWeight(weight)
    return font


class CameraCompassWidget(QLabel):
    TAPE_HEIGHT = 112

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: #03070b;")
        self._camera_pixmap: QPixmap | None = None
        self.heading: float | None = None
        self.heading_accuracy: float | None = None
        self.horizontal_fov = 74.0
        self.bearing_offset = 0.0

    def set_camera_image(self, data: bytes) -> bool:
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return False
        self._camera_pixmap = pixmap
        self.update()
        return True

    def set_heading(self, heading: float | None, accuracy: float | None = None) -> None:
        self.heading = heading
        self.heading_accuracy = accuracy
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        image_scale = self._draw_camera(painter)
        self._draw_compass(painter, image_scale)
        painter.end()

    def _draw_camera(self, painter: QPainter) -> float:
        width = self.width()
        height = self.height()
        if self._camera_pixmap is None or self._camera_pixmap.isNull():
            painter.fillRect(self.rect(), QColor("#03070b"))
            painter.setPen(QColor("#7f929f"))
            font = QFont()
            font.setPointSize(15)
            painter.setFont(font)
            painter.drawText(
                self.rect().adjusted(40, self.TAPE_HEIGHT, -40, -40),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                "Waiting for Sensor Logger camera data…\n"
                "Enable Camera + Compass and push to the URL in the status bar.",
            )
            return 1.0

        source_width = self._camera_pixmap.width()
        source_height = self._camera_pixmap.height()
        scale = max(width / source_width, height / source_height)
        draw_width = source_width * scale
        draw_height = source_height * scale
        target = QRectF(
            (width - draw_width) / 2.0,
            (height - draw_height) / 2.0,
            draw_width,
            draw_height,
        )
        painter.drawPixmap(target, self._camera_pixmap, QRectF(self._camera_pixmap.rect()))
        return scale

    def _draw_compass(self, painter: QPainter, image_scale: float) -> None:
        width = float(self.width())
        gradient = QLinearGradient(0.0, 0.0, 0.0, float(self.TAPE_HEIGHT))
        gradient.setColorAt(0.0, QColor(0, 8, 14, 220))
        gradient.setColorAt(0.7, QColor(0, 8, 14, 155))
        gradient.setColorAt(1.0, QColor(0, 8, 14, 0))
        painter.fillRect(QRectF(0.0, 0.0, width, self.TAPE_HEIGHT), gradient)

        baseline = 70.0
        tape_color = QColor("#88f4ff")
        painter.setPen(QPen(tape_color, 1.2))
        painter.drawLine(QPointF(0.0, baseline), QPointF(width, baseline))

        if self.heading is None:
            painter.setFont(overlay_font(11, QFont.Weight.DemiBold))
            painter.drawText(
                QRectF(0.0, 16.0, width, 30.0),
                Qt.AlignmentFlag.AlignCenter,
                "WAITING FOR COMPASS",
            )
            return

        display_heading = (self.heading + self.bearing_offset) % 360.0
        if self._camera_pixmap is not None and not self._camera_pixmap.isNull():
            focal = focal_length_pixels(
                float(self._camera_pixmap.width()),
                self.horizontal_fov,
            ) * image_scale
        else:
            focal = focal_length_pixels(width, self.horizontal_fov)

        painter.setFont(overlay_font(10, QFont.Weight.DemiBold))
        metrics = painter.fontMetrics()
        for mark in compass_marks(display_heading):
            x = project_delta_to_x(mark.delta, width / 2.0, focal)
            if not -20.0 <= x <= width + 20.0:
                continue
            tick_height = 30.0 if mark.is_major else 20.0 if mark.is_medium else 10.0
            painter.setPen(QPen(tape_color, 2.0 if mark.is_major else 1.2))
            painter.drawLine(QPointF(x, baseline), QPointF(x, baseline - tick_height))
            if mark.label is not None:
                label_width = metrics.horizontalAdvance(mark.label) + 12
                painter.drawText(
                    QRectF(x - label_width / 2.0, 10.0, label_width, 24.0),
                    Qt.AlignmentFlag.AlignCenter,
                    mark.label,
                )

        center_x = width / 2.0
        pointer_color = QColor("#ffcf5a")
        painter.setPen(QPen(pointer_color, 2.5))
        painter.drawLine(QPointF(center_x, 6.0), QPointF(center_x, baseline + 12.0))
        pointer = QPolygonF(
            [
                QPointF(center_x - 6.0, baseline + 8.0),
                QPointF(center_x + 6.0, baseline + 8.0),
                QPointF(center_x, baseline + 17.0),
            ]
        )
        painter.setBrush(pointer_color)
        painter.drawPolygon(pointer)

        readout = f"{display_heading:06.2f}° M"
        if self.heading_accuracy is not None and self.heading_accuracy >= 0:
            readout += f"  ±{self.heading_accuracy:.1f}°"
        painter.setFont(overlay_font(10, QFont.Weight.Bold))
        painter.setPen(pointer_color)
        painter.drawText(
            QRectF(center_x - 105.0, 82.0, 210.0, 22.0),
            Qt.AlignmentFlag.AlignCenter,
            readout,
        )


class MainWindow(QMainWindow):
    def __init__(self, push_url: str) -> None:
        super().__init__()
        self.setWindowTitle(f"DIY Astronomical Attic Observatory — v{__version__}")
        self.resize(1280, 800)
        self.viewer = CameraCompassWidget()
        self.setCentralWidget(self.viewer)
        self._push_url = push_url
        self._last_update_monotonic: float | None = None
        self._last_image_time: int | None = None
        self._build_status_bar()

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(500)
        self._refresh_status()

    def _build_status_bar(self) -> None:
        status = QStatusBar(self)
        status.setSizeGripEnabled(False)
        self.setStatusBar(status)

        self.connection_label = QLabel()
        self.connection_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        status.addWidget(self.connection_label, 1)

        status.addPermanentWidget(QLabel("Horizontal FOV"))
        self.fov_control = QDoubleSpinBox()
        self.fov_control.setRange(10.0, 160.0)
        self.fov_control.setDecimals(1)
        self.fov_control.setSingleStep(0.5)
        self.fov_control.setSuffix("°")
        self.fov_control.setValue(self.viewer.horizontal_fov)
        self.fov_control.valueChanged.connect(self._set_fov)
        status.addPermanentWidget(self.fov_control)

        status.addPermanentWidget(QLabel("Bearing offset"))
        self.offset_control = QDoubleSpinBox()
        self.offset_control.setRange(-180.0, 180.0)
        self.offset_control.setDecimals(1)
        self.offset_control.setSingleStep(0.5)
        self.offset_control.setSuffix("°")
        self.offset_control.valueChanged.connect(self._set_bearing_offset)
        status.addPermanentWidget(self.offset_control)

    @Slot(float)
    def _set_fov(self, value: float) -> None:
        self.viewer.horizontal_fov = value
        self.viewer.update()

    @Slot(float)
    def _set_bearing_offset(self, value: float) -> None:
        self.viewer.bearing_offset = value
        self.viewer.update()

    @Slot(object)
    def apply_sensor_update(self, update: SensorUpdate) -> None:
        self._last_update_monotonic = time.monotonic()
        if update.heading is not None:
            self.viewer.set_heading(update.heading, update.heading_accuracy)
        if update.image is not None and self.viewer.set_camera_image(update.image):
            self._last_image_time = update.image_timestamp_ns
        if update.horizontal_fov is not None:
            self.fov_control.setValue(update.horizontal_fov)
        self._refresh_status()

    def _refresh_status(self) -> None:
        if self._last_update_monotonic is None:
            state = "Listening"
        else:
            age = time.monotonic() - self._last_update_monotonic
            state = "Receiving" if age <= 3.0 else f"Waiting ({age:.0f}s since last push)"

        detail = ""
        if self._last_image_time is not None:
            image_time = datetime.fromtimestamp(self._last_image_time / 1_000_000_000)
            detail = f" · image {image_time:%H:%M:%S}"
        self.connection_label.setText(f"{state} · Sensor Logger URL: {self._push_url}{detail}")
