import queue
import shutil
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
ANDROID_DIR = APP_DIR / "android_studio"
APK_PATH = ANDROID_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
PACKAGE = "com.thequest.hotel"


def find_adb():
    candidates = [
        Path(shutil.which("adb")) if shutil.which("adb") else None,
        Path(Path.home()) / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
        Path("C:/Android/platform-tools/adb.exe"),
    ]
    return next((path for path in candidates if path is not None and path.exists()), None)


class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The Quest Hotel - Mobile Launcher")
        self.geometry("720x460")
        self.output = queue.Queue()
        self.server = None
        self.device = tk.StringVar(value="Not detected")
        self.status = tk.StringVar(value="Ready")
        self._build_ui()
        self.after(100, self._drain_output)
        self.refresh_devices()

    def _build_ui(self):
        ttk.Label(self, text="The Quest Hotel Mobile Deployment", font=("Segoe UI", 16, "bold")).pack(pady=14)
        ttk.Label(self, text="Flask PC server + Android WebView client").pack()
        row = ttk.Frame(self)
        row.pack(fill="x", padx=20, pady=18)
        ttk.Label(row, text="Device:").pack(side="left")
        ttk.Label(row, textvariable=self.device).pack(side="left", padx=8)
        ttk.Button(row, text="Refresh devices", command=self.refresh_devices).pack(side="right")
        buttons = ttk.Frame(self)
        buttons.pack(pady=8)
        ttk.Button(buttons, text="Start Flask server", command=self.start_server).grid(row=0, column=0, padx=5)
        ttk.Button(buttons, text="Build APK", command=self.build_apk).grid(row=0, column=1, padx=5)
        ttk.Button(buttons, text="Build, install && launch", command=self.deploy).grid(row=0, column=2, padx=5)
        ttk.Label(self, textvariable=self.status, foreground="#3B185F").pack(pady=8)
        self.log = tk.Text(self, height=14, state="disabled")
        self.log.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def write(self, text):
        self.output.put(text)

    def _drain_output(self):
        while not self.output.empty():
            self.log.configure(state="normal")
            self.log.insert("end", self.output.get())
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(100, self._drain_output)

    def run_async(self, command, callback=None, cwd=None):
        def worker():
            try:
                process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    self.write(line)
                code = process.wait()
                if callback:
                    self.after(0, lambda: callback(code))
            except OSError as error:
                self.write(f"{error}\n")
                if callback:
                    self.after(0, lambda: callback(1))
        threading.Thread(target=worker, daemon=True).start()

    def start_server(self):
        if self.server and self.server.poll() is None:
            self.status.set("Flask server is already running")
            return
        self.server = subprocess.Popen(
            ["python", str(APP_DIR / "run.py")], cwd=str(APP_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        self.status.set("Flask server running at http://localhost:5000")

    def refresh_devices(self):
        adb = find_adb()
        if not adb:
            self.device.set("ADB not found")
            return
        result = subprocess.run([str(adb), "devices"], capture_output=True, text=True)
        devices = [line.split()[0] for line in result.stdout.splitlines()
                   if "\tdevice" in line]
        self.device.set(", ".join(devices) if devices else "No authorized device")

    def build_apk(self):
        gradle = shutil.which("gradle")
        if not gradle:
            messagebox.showerror("Gradle not found", "Install Gradle or add it to PATH.")
            return
        self.status.set("Building APK...")
        self.run_async([gradle, "assembleDebug"], self._build_done, str(ANDROID_DIR))

    def _build_done(self, code):
        self.status.set("APK built" if code == 0 else "APK build failed")

    def deploy(self):
        adb = find_adb()
        if not adb:
            messagebox.showerror("ADB not found", "Install Android SDK Platform-Tools.")
            return
        self.start_server()
        gradle = shutil.which("gradle")
        if not gradle:
            messagebox.showerror("Gradle not found", "Install Gradle or add it to PATH.")
            return
        self.status.set("Building APK...")
        self.run_async([gradle, "assembleDebug"], lambda code: self._install(adb, code), str(ANDROID_DIR))

    def _install(self, adb, code):
        if code != 0 or not APK_PATH.exists():
            self.status.set("Deployment stopped: build failed")
            return
        reverse = subprocess.run([str(adb), "reverse", "tcp:5000", "tcp:5000"], capture_output=True, text=True)
        if reverse.returncode != 0:
            self.write(reverse.stderr)
        self.status.set("Installing APK...")
        self.run_async([str(adb), "install", "-r", str(APK_PATH)],
                       lambda result: self._launch(adb, result))

    def _launch(self, adb, code):
        if code != 0:
            self.status.set("APK installation failed")
            return
        subprocess.run([str(adb), "shell", "monkey", "-p", PACKAGE, "1"], check=False)
        self.status.set("App launched")


if __name__ == "__main__":
    Launcher().mainloop()
