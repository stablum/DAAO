from __future__ import annotations

from dataclasses import dataclass
import math


DIRECTION_LABELS = {
    0: "N",
    45: "NE",
    90: "E",
    135: "SE",
    180: "S",
    225: "SW",
    270: "W",
    315: "NW",
}


@dataclass(frozen=True, slots=True)
class CompassMark:
    heading: int
    delta: float
    label: str | None
    is_major: bool
    is_medium: bool


def normalize_heading(heading: float) -> float:
    """Normalize a heading to the half-open range [0, 360)."""
    return float(heading) % 360.0


def angular_delta(target: float, center: float) -> float:
    """Return the shortest signed clockwise angle from center to target."""
    delta = (normalize_heading(target) - normalize_heading(center) + 180.0) % 360.0 - 180.0
    if delta == -180.0:
        return 180.0
    return delta


def label_for_heading(heading: int) -> str | None:
    normalized = int(heading) % 360
    if normalized in DIRECTION_LABELS:
        return DIRECTION_LABELS[normalized]
    if normalized % 15 == 0:
        return f"{normalized:03d}°"
    return None


def compass_marks(center: float, maximum_delta: float = 89.0) -> tuple[CompassMark, ...]:
    """Build sorted five-degree compass marks around a center bearing."""
    marks = []
    for heading in range(0, 360, 5):
        delta = angular_delta(heading, center)
        if abs(delta) <= maximum_delta:
            marks.append(
                CompassMark(
                    heading=heading,
                    delta=delta,
                    label=label_for_heading(heading),
                    is_major=heading % 45 == 0,
                    is_medium=heading % 15 == 0,
                )
            )
    return tuple(sorted(marks, key=lambda mark: mark.delta))


def focal_length_pixels(image_width: float, horizontal_fov_degrees: float) -> float:
    """Compute pinhole focal length from image width and horizontal FOV."""
    if image_width <= 0:
        raise ValueError("image_width must be positive")
    if not 0.0 < horizontal_fov_degrees < 180.0:
        raise ValueError("horizontal_fov_degrees must be between 0 and 180")
    return image_width / (2.0 * math.tan(math.radians(horizontal_fov_degrees) / 2.0))


def project_delta_to_x(delta_degrees: float, center_x: float, focal_pixels: float) -> float:
    """Project an angular offset onto a pinhole image's horizontal axis."""
    if focal_pixels <= 0:
        raise ValueError("focal_pixels must be positive")
    if not -90.0 < delta_degrees < 90.0:
        raise ValueError("delta_degrees must be between -90 and 90")
    return center_x + focal_pixels * math.tan(math.radians(delta_degrees))
