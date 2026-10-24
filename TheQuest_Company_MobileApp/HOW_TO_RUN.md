# The Quest Android Studio App on a Pixel 6 Emulator

This is a native Android Studio/Kotlin application. It does **not** open
Chrome or another browser. The APK contains a small Flask service that runs
inside the Android process and the native login screen communicates with it
over localhost.

## 1. Open and build the Android Studio project

1. Install Android Studio with Android SDK Platform 35 and an Android SDK
   Build-Tools package.
2. Open this folder as the project:
   `TheQuest_Company_MobileApp/android_studio`
3. Let Gradle sync and accept the Chaquopy Python runtime download.
4. Choose the **Pixel 6** emulator in the device selector.
5. Click **Run**.

## 2. Install and launch on the Pixel 6 emulator

Android Studio builds, installs, and launches the APK directly. No browser and
no Windows Flask server are required.

## 3. Test login

Use one of the on-device demo accounts:

   - `admin` / `admin123`
   - `cashier` / `cashier123`
   - `kitchen` / `kitchen123`
   - `logistics` / `logistics123`
   - `utilities` / `utilities123`

This milestone implements native login first. Dashboards and role screens can
be migrated to Kotlin after login is verified on the emulator.

## Optional GUI launcher

On Windows, double-click `open_android_launcher.bat`. The launcher can:

- open the `android_studio` project in Android Studio;
- detect an authorized Pixel emulator or USB-debugged phone;
- build the debug APK;
- install the APK with ADB; and
- build, install, and launch the app in one action.

For a USB phone, enable **Developer options** and **USB debugging**, connect
the phone, accept the RSA prompt, then click **Refresh** in the launcher.
Android Studio and Android SDK Platform-Tools must be installed.
