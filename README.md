# DIY Astronomical Attic Observatory

DIY Astronomical Attic Observatory (DAAO) combines images from a phone camera
with the phone's sensor readings. Version **0.1.0** is the first desktop MVP:

- Python 3.14
- Qt 6.11.1 through the official PySide6 bindings
- an HTTP receiver on port 8000 for Sensor Logger
- a live Samsung Galaxy S23+ camera image
- a perspective-correct magnetic compass tape over the top of the image

## Install

Python 3.14 is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

## Run

```powershell
python -m daao
```

The status bar shows the URL to enter in Sensor Logger. It normally looks like:

```text
http://192.168.1.100:8000/data
```

The computer and phone must be on the same network. Windows may ask you to
allow Python through the firewall the first time the receiver starts.

## Configure Sensor Logger

In the Android Sensor Logger app:

1. Enable the **Camera** and **Compass** sensors.
2. Select the rear **Wide / 1x** camera on the Samsung Galaxy S23+.
3. Set the camera capture interval and HTTP batch period to one second.
4. Enable HTTP Push and enter the `/data` URL shown by DAAO.
5. Use **Tap to Test Pushing**, then start a recording and keep the app in the
   foreground while using the camera.

Sensor Logger sends `magneticBearing`, so the tape is relative to magnetic
north. Geographic/true-north correction belongs to a later astronomical
overlay milestone.

## Compass calibration

The center marker always represents the latest `magneticBearing` received from
Sensor Logger. Tape positions use pinhole-camera projection rather than a
linear degrees-per-pixel approximation.

The default horizontal field of view is 74 degrees, a practical starting value
for the Galaxy S23+ Wide / 1x camera. Use the **Horizontal FOV** control to
match the actual Sensor Logger camera crop. If Sensor Logger includes a
horizontal field-of-view value in its camera payload, DAAO applies it
automatically. **Bearing offset** is available for a measured mounting offset;
leave it at zero when the camera and compass reference are aligned.

## Supported incoming data

DAAO accepts Sensor Logger's JSON batch schema at `POST /data`, including:

```json
{
  "messageId": 1,
  "sessionId": "recording-id",
  "deviceId": "phone-id",
  "payload": [
    {
      "name": "compass",
      "time": 1785000000000000000,
      "values": {"magneticBearing": 135.0}
    }
  ]
}
```

The app also accepts camera images as base64/data-URI fields in a camera
reading, as raw `image/*` request bodies, or in multipart requests. This keeps
the receiver compatible with Sensor Logger's newer image streaming while its
published schema is evolving. Requests are limited to 32 MiB.

`GET /health` returns a small health response.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The suite covers payload parsing, image decoding, compass wrap-around and
projection, the HTTP endpoint, and a headless Qt widget smoke test.
