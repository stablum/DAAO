# DIY Astronomical Attic Observatory

DIY Astronomical Attic Observatory (DAAO) combines images from a phone camera
with the phone's orientation sensors. Version **0.2.0** consists of:

- a Python 3.14 desktop receiver and Qt 6.11.1 GUI;
- a private, native Android camera-and-orientation sender;
- one synchronized HTTP update per second over the local network;
- a perspective-correct magnetic compass tape over the camera image.

The Android app uses CameraX and Android's rotation-vector sensor. It calculates
the azimuth of the rear camera's viewing direction and also sends elevation,
pitch, roll, the full orientation quaternion, sensor accuracy, and timestamps.
The extra pose data is retained in the protocol for future astronomical
overlays even though version 0.2.0 displays only the camera and compass.

No paid application, cloud service, account, or Google Play publication is
required. The private APK can be installed directly with Android Debug Bridge
(ADB).

## Desktop requirements

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- Windows, Linux, or macOS with the phone on the same local network

On Windows, install uv with:

```powershell
winget install --id=astral-sh.uv -e
```

Create the locked Python environment:

```powershell
uv sync --locked
```

## Run the desktop application

```powershell
uv run --locked daao
```

DAAO listens on TCP port 8000. Its status bar displays the address to enter in
the Android app, normally:

```text
http://192.168.1.100:8000/data
```

The computer and phone must be on the same network. Allow Python to receive
private-network traffic if the operating-system firewall asks.

## Build the Android application

The repository includes the Gradle wrapper, so Android Studio is not needed for
routine command-line builds once the Android SDK and JDK 17 are installed.

From the repository root:

```powershell
.\android\gradlew.bat -p .\android :app:assembleDebug
```

The resulting APK is:

```text
android\app\build\outputs\apk\debug\app-debug.apk
```

The debug APK is automatically signed with the computer's Android debug key.
Updates must use the same signing key. Before distributing DAAO or registering
its package name, create a separately backed-up release key and never commit
that key or its password to Git.

## Install with ADB

On the Samsung Galaxy S23+:

1. Open **Settings → About phone → Software information**.
2. Tap **Build number** seven times to enable Developer options.
3. Open **Settings → Developer options** and enable **USB debugging**.
4. Connect the phone by USB and approve the computer when Android asks.

Then install or update DAAO:

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices
& $adb install -r .\android\app\build\outputs\apk\debug\app-debug.apk
```

ADB installation does not require Google Play publication, Android developer
registration, or a fee. The cable can be disconnected and USB debugging can be
disabled after installation.

## Use DAAO Camera

1. Start the Python desktop application.
2. Open **DAAO Camera** on the phone and grant camera permission.
3. Enter the complete URL shown in the desktop status bar.
4. Confirm that the rear-camera preview and an orientation reading appear.
5. Tap **Start streaming**.

The phone screen stays awake while the app is open. The status panel reports the
HTTP response, frame number, and JPEG size. A successful connection normally
shows `HTTP 200`. The URL is remembered for the next run.

The app currently runs in the foreground. Android may stop access to the camera
when another app takes ownership of it or DAAO Camera is sent to the background.

## Compass calibration

The center marker represents the magnetic azimuth of the rear camera's optical
axis. Tape positions use pinhole-camera projection rather than a linear
degrees-per-pixel approximation.

The default horizontal field of view is 74 degrees, a practical starting value
for the Galaxy S23+ Wide / 1x camera. Use the desktop **Horizontal FOV** control
to calibrate the actual camera crop. **Bearing offset** compensates for a
measured magnetic or mounting offset.

The reading is relative to magnetic north. Geographic declination, camera
intrinsics, and star-coordinate transformation belong to a later astronomical
overlay milestone. Magnetic heading is mathematically undefined when the
camera points exactly vertically; the transmitted quaternion remains valid in
that orientation.

## DAAO mobile protocol

The phone sends `multipart/form-data` to `POST /data`. Each request contains:

- a `data` part with JSON sensor and timing information;
- an `image` part with the corresponding JPEG frame.

The JSON uses the protocol identifier `daao-mobile-v1` and includes compatible
`compass`, `orientation`, and `camera` readings:

```json
{
  "protocol": "daao-mobile-v1",
  "messageId": 1,
  "sessionId": "recording-id",
  "deviceId": "samsung SM-S916B",
  "imageTimestampNs": 1785000000000000000,
  "payload": [
    {
      "name": "compass",
      "time": 1785000000000000000,
      "values": {
        "magneticBearing": 135.0,
        "headingAccuracy": 3.0
      }
    },
    {
      "name": "orientation",
      "time": 1785000000000000000,
      "values": {
        "cameraElevation": 25.0,
        "quaternionW": 1.0,
        "quaternionX": 0.0,
        "quaternionY": 0.0,
        "quaternionZ": 0.0
      }
    },
    {
      "name": "camera",
      "time": 1785000000000000000,
      "values": {"horizontalFov": 74.0}
    }
  ]
}
```

Requests are limited to 32 MiB. `GET /health` returns a small health response.

## Sensor Logger compatibility

The desktop receiver remains compatible with Sensor Logger JSON batches, raw
`image/*` bodies, base64/data-URI camera fields, and multipart image requests.
Sensor Logger 1.62 was observed to save camera images locally while omitting
them from HTTP Push, which is why DAAO now has its own Android sender.

## Diagnostic log

DAAO keeps a rotating diagnostic log without saving request bodies or camera
images. On Windows it is written to:

```text
%LOCALAPPDATA%\DAAO\logs\daao.log
```

Each request records its source, content type, size, response outcome, sensor
reading count, and whether a compass heading or image was recognized. Set
`DAAO_LOG_DIR` before starting DAAO to use another directory.

## Tests

Run the Python tests:

```powershell
uv run --locked python -m unittest discover -s tests -v
```

Run Android unit tests:

```powershell
.\android\gradlew.bat -p .\android :app:testDebugUnitTest
```

Build the Python source and wheel distributions with:

```powershell
uv build
```
