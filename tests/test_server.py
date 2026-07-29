from http.client import HTTPConnection
import json
import threading
import unittest

from daao.server import SensorServer


class ServerTests(unittest.TestCase):
    def test_health_and_sensor_post(self) -> None:
        received = []
        event = threading.Event()

        def on_update(update: object) -> None:
            received.append(update)
            event.set()

        with SensorServer(host="127.0.0.1", port=0, on_update=on_update) as server:
            connection = HTTPConnection("127.0.0.1", server.port, timeout=2)
            connection.request("GET", "/health")
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())["status"], "ok")

            body = json.dumps(
                {
                    "payload": [
                        {
                            "name": "compass",
                            "time": 1,
                            "values": {"magneticBearing": 270},
                        }
                    ]
                }
            ).encode()
            with self.assertLogs("daao.server", level="INFO") as captured:
                connection.request(
                    "POST",
                    "/data",
                    body=body,
                    headers={"Content-Type": "application/json"},
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()
            connection.close()

            self.assertTrue(event.wait(1))
            self.assertEqual(received[0].heading, 270)
            self.assertTrue(
                any(
                    "Accepted sensor update" in message
                    and "readings=1" in message
                    and "heading=270.0" in message
                    for message in captured.output
                )
            )

    def test_rejects_wrong_endpoint(self) -> None:
        with SensorServer(host="127.0.0.1", port=0) as server:
            connection = HTTPConnection("127.0.0.1", server.port, timeout=2)
            connection.request(
                "POST",
                "/wrong",
                body=b"{}",
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 404)
            response.read()
            connection.close()


if __name__ == "__main__":
    unittest.main()
