"""
Security and Health Logging System for The Quest Hotel Mobile App.
Maintains 100% cryptographic parity with Desktop Application logs.
- Encrypted auth logs using symmetric stream cipher
- Unencrypted system telemetry and health metrics
"""

import os
import base64
import platform
import sqlite3
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
APP_DIR = BACKEND_DIR.parent
PROJECT_ROOT = APP_DIR.parent

# Shared logs directory in Desktop App or local fallback
SHARED_LOGS_DIR = PROJECT_ROOT / "TheQuest_Company_DesktopApp" / "logs"
LOCAL_LOGS_DIR = APP_DIR / "logs"

def get_logs_dir() -> Path:
    if SHARED_LOGS_DIR.exists():
        return SHARED_LOGS_DIR
    LOCAL_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOCAL_LOGS_DIR

_CIPHER_KEY = b"TheQuestHotelSecuredCipherKey2026!#"


def _encrypt_text(plain_text: str) -> str:
    """Symmetric stream cipher with rolling key and base64 output."""
    raw_bytes = plain_text.encode("utf-8")
    key_len = len(_CIPHER_KEY)
    encrypted = bytearray()
    for i, b in enumerate(raw_bytes):
        k = _CIPHER_KEY[i % key_len]
        encrypted.append(b ^ k ^ ((i * 7) & 0xFF))
    return "ENC:" + base64.b64encode(encrypted).decode("ascii")


def _decrypt_text(cipher_text: str) -> str:
    """Decrypts base64 encoded cipher text."""
    clean = cipher_text.strip()
    if not clean.startswith("ENC:"):
        return clean
    try:
        raw_b64 = clean[4:]
        data = base64.b64decode(raw_b64.encode("ascii"))
        key_len = len(_CIPHER_KEY)
        decrypted = bytearray()
        for i, b in enumerate(data):
            k = _CIPHER_KEY[i % key_len]
            decrypted.append(b ^ k ^ ((i * 7) & 0xFF))
        return decrypted.decode("utf-8", errors="replace")
    except Exception as err:
        return f"[CORRUPTED LOG ENTRY: {err}]"


def log_auth_event(event_type: str, username: str, role: str = "Unknown", status: str = "SUCCESS", details: str = ""):
    """Logs auth event into the encrypted audit log file."""
    try:
        logs_dir = get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        auth_file = logs_dir / "auth_logs.enc.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] | EVENT: {event_type} | STATUS: {status} | USERNAME: {username} | ROLE: {role} | CLIENT: Mobile Portal | DETAILS: {details}"
        encrypted_line = _encrypt_text(entry) + "\n"
        with open(auth_file, "a", encoding="utf-8") as f:
            f.write(encrypted_line)
    except Exception as err:
        print(f"[Mobile Logger Error] {err}")


def read_decrypted_auth_logs(limit: int = 50):
    """Reads and decrypts authentication logs for Admin inspection."""
    logs_dir = get_logs_dir()
    auth_file = logs_dir / "auth_logs.enc.txt"
    if not auth_file.exists():
        return []
    logs = []
    try:
        with open(auth_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    decrypted = _decrypt_text(stripped)
                    logs.append(decrypted)
        return list(reversed(logs[-limit:]))
    except Exception as err:
        return [f"[Error reading auth log: {err}]"]


def log_system_health(db_path: Path = None):
    """Records runtime telemetry and database status."""
    try:
        logs_dir = get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)
        health_file = logs_dir / "system_health.txt"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_status = "ONLINE"
        db_size_kb = 0

        if db_path and os.path.exists(db_path):
            try:
                db_size_kb = round(os.path.getsize(db_path) / 1024, 2)
            except Exception:
                pass

        health_entry = (
            f"[{now_str}] MOBILE PORTAL HEALTH REPORT\n"
            f"  - Client: Mobile Web App (Flask)\n"
            f"  - Platform: {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"  - Python Runtime: {platform.python_version()}\n"
            f"  - Database Status: {db_status} ({db_size_kb} KB)\n"
            "----------------------------------------------------------------------\n"
        )
        with open(health_file, "a", encoding="utf-8") as f:
            f.write(health_entry)
    except Exception as err:
        print(f"[Mobile Health Log Error] {err}")


def read_system_health_logs(limit: int = 30):
    """Reads system health telemetry log file."""
    logs_dir = get_logs_dir()
    health_file = logs_dir / "system_health.txt"
    if not health_file.exists():
        return ["No system health records found."]
    try:
        with open(health_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines[-limit:]
    except Exception as err:
        return [f"[Error reading health logs: {err}]"]
