"""
The Quest Hotel - Mobile Application Portal Runner.
Verifies environment, detects local network IP for mobile device access,
launches browser, and starts Flask web server on port 5001.
"""

import sys
import time
import socket
import webbrowser
import threading
import os
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))


def get_local_ip() -> str:
    """Detect LAN IP address so phones on the same Wi-Fi can connect."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def open_browser(port: int):
    """Wait for server socket to initialize, then launch web browser."""
    time.sleep(1.2)
    url = f"http://127.0.0.1:{port}"
    print(f"\n[The Quest] Launching browser to {url} ...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[The Quest] Note: Could not auto-launch browser ({e}).")
        print(f"[The Quest] Please navigate manually to: {url}")


def verify_environment(port: int):
    """Check dependencies and database integrity."""
    print("=" * 72)
    print("  THE QUEST HOTEL - MOBILE MANAGEMENT SYSTEM PORTAL")
    print('  "We shall never deny a guest, even the most ridiculous request"')
    print("=" * 72)

    try:
        import flask
        print(f"[OK] Flask {flask.__version__} loaded.")
    except ImportError:
        print("[ERROR] Flask is not installed.")
        print("Please install requirements using:")
        print("    pip install -r requirements.txt")
        sys.exit(1)

    try:
        import fpdf
        print(f"[OK] FPDF {fpdf.__version__} audit report generator loaded.")
    except ImportError:
        print("[WARN] fpdf package missing; PDF exports will be unavailable.")

    # Check database
    from backend.db import get_db_path, init_database_if_needed
    db_file = get_db_path()
    if db_file.exists():
        print(f"[OK] SQLite Database located: {db_file}")
    else:
        print(f"[INFO] Initializing new database at {db_file}...")
        init_database_if_needed()

    local_ip = get_local_ip()
    print("-" * 72)
    print(f"  Local Computer Access:  http://127.0.0.1:{port}")
    print(f"  Pixel 6 Emulator:      http://10.0.2.2:{port}")
    print(f"  Mobile Phone / Wi-Fi:   http://{local_ip}:{port}")
    print("-" * 72)
    print("  Demo Logins: admin/admin123 • cashier/cashier123 • kitchen/kitchen123")
    print("               logistics/logistics123 • utilities/utilities123")
    print("=" * 72)


def main():
    port = int(os.environ.get("PORT", "5001"))
    verify_environment(port)

    # Launch browser in background thread
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    from app import app
    print(f"\n[The Quest Mobile] Server online at http://0.0.0.0:{port}")
    print("[The Quest Mobile] Press Ctrl+C in terminal to stop server.\n")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
