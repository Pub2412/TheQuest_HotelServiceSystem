"""The Quest Android Studio launcher.

Provides a small Windows GUI for opening, building, installing, and launching
the Android Studio project on an emulator or an ADB-enabled phone.
"""

import os
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
ANDROID_DIR = APP_DIR / "android_studio"
PACKAGE_NAME = "com.thequest.hotel"
MAIN_ACTIVITY = "com.thequest.hotel/.MainActivity"
ADB_CANDIDATES = [
    Path(os.environ.get("ANDROID_HOME", "")) / "platform-tools" / "adb.exe",
    Path(os.environ.get("ANDROID_SDK_ROOT", "")) / "platform-tools" / "adb.exe",
]
STUDIO_CANDIDATES = [
    Path(os.environ.get("ProgramFiles", "")) / "Android" / "Android Studio" / "bin" / "studio64.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Android Studio" / "bin" / "studio64.exe",
]


def find_executable(name, candidates):
    on_path = shutil.which(name)
    if on_path:
        return Path(on_path)
    return next((path for path in candidates if path.is_file()), None)


def run_command(command, output_queue):
    try:
        process = subprocess.Popen(
            command,
            cwd=str(ANDROID_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
        for line in process.stdout:
            output_queue.put(line.rstrip())
        result = process.wait()
        output_queue.put("[Finished with exit code {}]".format(result))
    except OSError as error:
        output_queue.put("[ERROR] {}".format(error))


class AndroidLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The Quest Hotel - Android Launcher")
        self.geometry("760x520")
        self.minsize(620, 420)
        self.output_queue = queue.Queue()
        self.device_var = tk.StringVar(value="No device detected")
        self.status_var = tk.StringVar(value="Ready")
        self._build_ui()
        self.after(100, self._drain_output)
        self.detect_devices()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = ttk.Frame(self, padding=16)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header, text="THE QUEST HOTEL", font=("Segoe UI", 18, "bold")
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header, text="Android Studio / Pixel 6 / USB deployment"
        ).grid(row=1, column=0, sticky="w")

        controls = ttk.LabelFrame(self, text="Project and device", padding=12)
        controls.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Project:").grid(row=0, column=0, sticky="w")
        ttk.Label(controls, text=str(ANDROID_DIR)).grid(row=0, column=1, columnspan=2, sticky="w")
        ttk.Label(controls, text="Device:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Label(controls, textvariable=self.device_var).grid(
            row=1, column=1, sticky="w", pady=(10, 0)
        )
        ttk.Button(controls, text="Refresh", command=self.detect_devices).grid(
            row=1, column=2, padx=(8, 0), pady=(10, 0)
        )

        actions = ttk.Frame(self, padding=(16, 0, 16, 10))
        actions.grid(row=2, column=0, sticky="nsew")
        actions.columnconfigure(0, weight=1)
        actions.rowconfigure(1, weight=1)
        buttons = ttk.Frame(actions)
        buttons.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for index in range(4):
            buttons.columnconfigure(index, weight=1)
        ttk.Button(buttons, text="Open Android Studio", command=self.open_studio).grid(
            row=0, column=0, padx=3, sticky="ew"
        )
        ttk.Button(buttons, text="Build APK", command=self.build_apk).grid(
            row=0, column=1, padx=3, sticky="ew"
        )
        ttk.Button(buttons, text="Install APK", command=self.install_apk).grid(
            row=0, column=2, padx=3, sticky="ew"
        )
        ttk.Button(buttons, text="Build + Install + Run", command=self.build_install_run).grid(
            row=0, column=3, padx=3, sticky="ew"
        )

        self.output = tk.Text(actions, height=16, state="disabled", wrap="word")
        self.output.grid(row=1, column=0, sticky="nsew")
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w").grid(
            row=3, column=0, sticky="ew"
        )

    def write(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def _drain_output(self):
        while not self.output_queue.empty():
            self.write(self.output_queue.get_nowait())
        self.after(100, self._drain_output)

    def adb_path(self):
        adb = find_executable("adb", ADB_CANDIDATES)
        if not adb:
            messagebox.showerror(
                "ADB not found",
                "Install Android SDK Platform-Tools and set ANDROID_HOME, "
                "ANDROID_SDK_ROOT, or add platform-tools to PATH.",
            )
        return adb

    def detect_devices(self):
        adb = self.adb_path()
        if not adb:
            self.device_var.set("ADB not found")
            return
        try:
            result = subprocess.run(
                [str(adb), "devices"],
                capture_output=True,
                text=True,
                check=True,
            )
            devices = [
                line.split()[0]
                for line in result.stdout.splitlines()
                if "\tdevice" in line
            ]
            self.device_var.set(", ".join(devices) if devices else "No authorized device")
            self.write("Detected devices: {}".format(self.device_var.get()))
        except (OSError, subprocess.CalledProcessError) as error:
            self.device_var.set("ADB error")
            self.write("[ERROR] {}".format(error))

    def open_studio(self):
        studio = find_executable("studio64.exe", STUDIO_CANDIDATES)
        if not studio:
            studio = find_executable("studio", [])
        if not studio:
            messagebox.showerror(
                "Android Studio not found",
                "Install Android Studio or add its bin folder to PATH.",
            )
            return
        subprocess.Popen([str(studio), str(ANDROID_DIR)])
        self.status_var.set("Android Studio opened")

    def gradle_command(self):
        wrapper = ANDROID_DIR / "gradlew.bat"
        if wrapper.is_file():
            return [str(wrapper)]
        gradle = shutil.which("gradle")
        if gradle:
            return [gradle]
        messagebox.showerror(
            "Gradle not found",
            "Open the project in Android Studio and let Gradle sync, or install "
            "Gradle and add it to PATH.",
        )
        return None

    def build_apk(self, on_complete=None):
        command = self.gradle_command()
        if not command:
            return
        self.status_var.set("Building debug APK...")
        build_thread = threading.Thread(
            target=run_command,
            args=(command + ["assembleDebug"], self.output_queue),
            daemon=True,
        )
        build_thread.start()
        if on_complete:
            self.after(100, lambda: self._wait_for_build(build_thread, on_complete))

    def _wait_for_build(self, thread, callback):
        if thread.is_alive():
            self.after(200, lambda: self._wait_for_build(thread, callback))
        else:
            callback()

    def apk_path(self):
        apk = ANDROID_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
        if not apk.is_file():
            messagebox.showwarning("APK not found", "Build the debug APK first.")
            return None
        return apk

    def install_apk(self, launch=True):
        adb = self.adb_path()
        apk = self.apk_path()
        if not adb or not apk:
            return
        self.status_var.set("Installing APK...")
        command = [str(adb), "install", "-r", str(apk)]
        install_thread = threading.Thread(
            target=run_command, args=(command, self.output_queue), daemon=True
        )
        install_thread.start()
        if launch:
            self.after(100, lambda: self._wait_for_install(install_thread, adb))

    def _wait_for_install(self, thread, adb):
        if thread.is_alive():
            self.after(200, lambda: self._wait_for_install(thread, adb))
            return
        self.status_var.set("Launching app...")
        launch_command = [str(adb), "shell", "monkey", "-p", PACKAGE_NAME, "1"]
        threading.Thread(
            target=run_command,
            args=(launch_command, self.output_queue),
            daemon=True,
        ).start()

    def build_install_run(self):
        self.build_apk(on_complete=lambda: self.install_apk(launch=True))


if __name__ == "__main__":
    AndroidLauncher().mainloop()
