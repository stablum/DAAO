import math
import unittest

from daao.compass import (
    angular_delta,
    compass_marks,
    focal_length_pixels,
    label_for_heading,
    normalize_heading,
    project_delta_to_x,
)


class CompassTests(unittest.TestCase):
    def test_normalizes_heading(self) -> None:
        self.assertEqual(normalize_heading(360), 0)
        self.assertEqual(normalize_heading(-10), 350)
        self.assertEqual(normalize_heading(725), 5)

    def test_shortest_delta_wraps_across_north(self) -> None:
        self.assertEqual(angular_delta(5, 355), 10)
        self.assertEqual(angular_delta(355, 5), -10)
        self.assertEqual(angular_delta(180, 0), 180)

    def test_cardinal_and_intercardinal_labels(self) -> None:
        expected = {
            0: "N",
            45: "NE",
            90: "E",
            135: "SE",
            180: "S",
            225: "SW",
            270: "W",
            315: "NW",
        }
        for heading, label in expected.items():
            self.assertEqual(label_for_heading(heading), label)
        self.assertEqual(label_for_heading(30), "030°")
        self.assertIsNone(label_for_heading(35))

    def test_marks_are_sorted_around_wrapped_heading(self) -> None:
        marks = compass_marks(358, maximum_delta=10)
        self.assertEqual([mark.heading for mark in marks], [350, 355, 0, 5])
        self.assertEqual([mark.delta for mark in marks], [-8, -3, 2, 7])

    def test_pinhole_projection_hits_fov_edges(self) -> None:
        focal = focal_length_pixels(1000, 90)
        self.assertTrue(math.isclose(focal, 500, rel_tol=1e-12))
        self.assertTrue(
            math.isclose(project_delta_to_x(-45, 500, focal), 0, abs_tol=1e-9)
        )
        self.assertTrue(
            math.isclose(project_delta_to_x(45, 500, focal), 1000, abs_tol=1e-9)
        )


if __name__ == "__main__":
    unittest.main()
