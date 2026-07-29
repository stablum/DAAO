import base64
import json
import unittest

from daao.parsing import PayloadError, parse_http_payload, parse_sensor_logger_message


JPEG = b"\xff\xd8\xff\xe0" + b"test-jpeg"
PNG = b"\x89PNG\r\n\x1a\n" + b"test-png"


class ParsingTests(unittest.TestCase):
    def test_documented_compass_payload(self) -> None:
        update = parse_sensor_logger_message(
            {
                "messageId": 17,
                "sessionId": "session",
                "deviceId": "s23-plus",
                "payload": [
                    {
                        "name": "compass",
                        "time": 100,
                        "accuracy": 3,
                        "values": {"magneticBearing": 361.25},
                    }
                ],
            }
        )
        self.assertEqual(update.heading, 1.25)
        self.assertEqual(update.heading_accuracy, 3)
        self.assertEqual(update.message_id, 17)
        self.assertEqual(update.session_id, "session")
        self.assertEqual(update.device_id, "s23-plus")

    def test_latest_timestamp_wins_when_batch_is_out_of_order(self) -> None:
        update = parse_sensor_logger_message(
            {
                "payload": [
                    {"name": "compass", "time": 200, "values": {"magneticBearing": 20}},
                    {"name": "compass", "time": 100, "values": {"magneticBearing": 10}},
                ]
            }
        )
        self.assertEqual(update.heading, 20)

    def test_location_bearing_is_not_compass_heading(self) -> None:
        update = parse_sensor_logger_message(
            {
                "payload": [
                    {"name": "compass", "time": 100, "values": {"magneticBearing": 25}},
                    {"name": "location", "time": 200, "values": {"bearing": 180}},
                ]
            }
        )
        self.assertEqual(update.heading, 25)

    def test_camera_data_uri_and_fov(self) -> None:
        encoded = base64.b64encode(JPEG).decode("ascii")
        update = parse_sensor_logger_message(
            {
                "payload": [
                    {
                        "name": "camera",
                        "time": 123,
                        "values": {
                            "data": f"data:image/jpeg;base64,{encoded}",
                            "horizontalFov": 73.5,
                        },
                    }
                ]
            }
        )
        self.assertEqual(update.image, JPEG)
        self.assertEqual(update.image_timestamp_ns, 123)
        self.assertEqual(update.horizontal_fov, 73.5)

    def test_raw_image_body(self) -> None:
        update = parse_http_payload("image/png", PNG)
        self.assertEqual(update.image, PNG)

    def test_multipart_json_and_image(self) -> None:
        boundary = "daao-test-boundary"
        json_part = json.dumps(
            {"payload": [{"name": "compass", "values": {"magneticBearing": 90}}]}
        ).encode()
        body = (
            f"--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"data\"\r\n"
            "Content-Type: application/json\r\n\r\n"
        ).encode() + json_part + (
            f"\r\n--{boundary}\r\n"
            "Content-Disposition: form-data; name=\"image\"; filename=\"frame.png\"\r\n"
            "Content-Type: image/png\r\n\r\n"
        ).encode() + PNG + f"\r\n--{boundary}--\r\n".encode()
        update = parse_http_payload(f"multipart/form-data; boundary={boundary}", body)
        self.assertEqual(update.heading, 90)
        self.assertEqual(update.image, PNG)

    def test_json_body(self) -> None:
        body = json.dumps(
            {"payload": [{"name": "compass", "values": {"magneticBearing": -5}}]}
        ).encode()
        update = parse_http_payload("application/json; charset=utf-8", body)
        self.assertEqual(update.heading, 355)

    def test_rejects_invalid_json(self) -> None:
        with self.assertRaises(PayloadError):
            parse_http_payload("application/json", b"{")

    def test_test_push_without_readings_is_accepted(self) -> None:
        update = parse_sensor_logger_message({"message": "test"})
        self.assertEqual(update.reading_count, 0)
        self.assertIsNone(update.heading)


if __name__ == "__main__":
    unittest.main()
