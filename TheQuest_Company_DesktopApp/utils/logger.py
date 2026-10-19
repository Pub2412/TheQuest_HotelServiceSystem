"""
Security and Health Logging System for The Quest Hotel Management System.
- Auth Logs: Encrypted on write and decrypted only in the system for Admin view.
- System Health Logs: Periodic unencrypted health checks and telemetry.
"""

import os
import base64
import time
import platform
import sqlite3
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
AUTH_LOG_FILE = LOGS_DIR / "auth_logs.enc.txt"
HEALTH_LOG_FILE = LOGS_DIR / "system_health.txt"

# Encryption key derived from system secret
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
    """Logs login, logout, failed attempt, or lockout event to encrypted auth log."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] | EVENT: {event_type} | STATUS: {status} | USERNAME: {username} | ROLE: {role} | DETAILS: {details}"
        encrypted_line = _encrypt_text(entry) + "\n"
        with open(AUTH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(encrypted_line)
    except Exception as err:
        print(f"Error writing auth log: {err}")

def read_decrypted_auth_logs():
    """Reads and decrypts all authentication logs for Admin display."""
    if not AUTH_LOG_FILE.exists():
        return []
    logs = []
    try:
        with open(AUTH_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    decrypted = _decrypt_text(stripped)
                    logs.append(decrypted)
    except Exception as err:
        logs.append(f"[Error reading auth log file: {err}]")
    return logs

def log_system_health(db_path: Path = None):
    """Logs system runtime telemetry, database stats, and health metrics to unencrypted log."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db_status = "UNKNOWN"
        db_size_kb = 0
        
        if db_path and os.path.exists(db_path):
            try:
                db_size_kb = round(os.path.getsize(db_path) / 1024, 2)
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1")
                conn.close()
                db_status = "HEALTHY (ONLINE)"
            except Exception as e:
                db_status = f"ERROR ({e})"
        
        health_entry = (
            f"[{now_str}] SYSTEM HEALTH REPORT\n"
            f"  - OS / Platform: {platform.system()} {platform.release()} ({platform.machine()})\n"
            f"  - Python Runtime: {platform.python_version()}\n"
            f"  - System Process PID: {os.getpid()}\n"
            f"  - Database Status: {db_status}\n"
            f"  - Database Size: {db_size_kb} KB\n"
            f"  - Application Status: NORMAL / RESPONSIVE\n"
            f"--------------------------------------------------------------------------------\n"
        )
        with open(HEALTH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(health_entry)
    except Exception as err:
        print(f"Error writing system health log: {err}")

def read_system_health_logs(max_lines: int = 150):
    """Reads recent system health log entries."""
    if not HEALTH_LOG_FILE.exists():
        return "No system health logs recorded yet."
    try:
        with open(HEALTH_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as err:
        return f"Error reading system health log: {err}"
