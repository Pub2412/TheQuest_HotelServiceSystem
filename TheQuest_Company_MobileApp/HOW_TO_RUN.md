# The Quest mobile app

This port uses the recommended deployment model:

1. Flask runs on the development computer and uses the shared
   `database/hotel_service.db`.
2. The Android APK is a small WebView client.
3. The launcher detects an authorized emulator or USB-debugged phone, runs
   `adb reverse tcp:5000 tcp:5000`, builds the APK, installs it, and launches
   it.

## Setup

- Install Python and run `pip install -r requirements.txt` from this folder.
- Install Android SDK Platform 35, Build Tools, Gradle, and Platform-Tools.
- Add `gradle` and `adb` to `PATH`, or install them in the standard Android SDK
  locations.
- For a phone, enable Developer options and USB debugging, connect it, and
  accept the RSA authorization prompt.

## Start

Run `open_mobile_launcher.bat`, then choose **Build, install & launch**.
The launcher does not open Android Studio. Select the Pixel 6 emulator in the
Android Device Manager before deployment, or connect the USB phone first.

The Flask service is available at `http://localhost:5000` on the PC. The
emulator uses `10.0.2.2`; an authorized USB device uses the reverse ADB tunnel.
