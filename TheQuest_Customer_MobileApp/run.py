import os
import sys
from pathlib import Path

# Add project root to sys.path
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = APP_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"============================================================")
    print(f" The Quest Hotel - Customer Mobile Application")
    print(f" Running at: http://localhost:{port} (or http://10.0.2.2:{port} on emulator)")
    print(f"============================================================")
    app.run(host="0.0.0.0", port=port, debug=False)

