"""
The Quest Hotel - Customer Website Runner Script.
Automatically checks dependencies, verifies database connection, opens browser,
and runs the Flask web server on http://127.0.0.1:5000
"""

import sys
import time
import webbrowser
import threading
from pathlib import Path

# Set up project paths
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

def open_browser():
    """Wait for server to bind then launch the web browser."""
    time.sleep(1.5)
    url = "http://127.0.0.1:5000"
    print(f"\n[The Quest] Launching browser to {url} ...")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[The Quest] Could not automatically open browser: {e}")
        print(f"[The Quest] Please manually navigate to: {url}")

def check_environment():
    """Verify that dependencies and the SQLite database file exist."""
    print("=" * 70)
    print("  THE QUEST HOTEL - CUSTOMER WEBSITE PORTAL")
    print('  "We shall never deny a guest, even the most ridiculous request"')
    print("=" * 70)

    try:
        import flask
        print(f"[OK] Flask {flask.__version__} is installed and ready.")
    except ImportError:
        print("[ERROR] Flask is not installed.")
        print("Please install requirements using:")
        print("    pip install -r requirements.txt")
        sys.exit(1)

    db_file = PROJECT_ROOT / "database" / "hotel_service.db"
    if db_file.exists():
        print(f"[OK] SQLite Database located: {db_file}")
    else:
        print(f"[WARN] Database file not found at {db_file}")
        print("[INFO] Attempting to initialize database from setup_db...")
        try:
            sys.path.insert(0, str(PROJECT_ROOT / "database"))
            from setup_db import create_database
            create_database()
            print("[OK] Database successfully initialized.")
        except Exception as e:
            print(f"[ERROR] Could not initialize database: {e}")

    assets_dir = PROJECT_ROOT / "assets"
    if assets_dir.exists():
        print(f"[OK] Assets directory located: {assets_dir}")
    else:
        print(f"[WARN] Assets directory not found at {assets_dir}")

def main():
    check_environment()

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and run Flask app
    from app import app
    print("\n[The Quest] Server online at http://127.0.0.1:5000")
    print("[The Quest] Press Ctrl+C to terminate the web server.\n")
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    main()
