import hashlib
import hmac
import sqlite3
import threading
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
database_path = None


def _hash_password(password):
    salt = hashlib.sha256(password.encode("utf-8")).digest()[:16]
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return "{}${}".format(salt.hex(), digest.hex())


def _verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 100000
        )
        return hmac.compare_digest(actual, bytes.fromhex(hash_hex))
    except (TypeError, ValueError):
        return hmac.compare_digest(password, stored_hash)


def _initialize_database():
    connection = sqlite3.connect(str(database_path))
    connection.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, "
        "password_hash TEXT NOT NULL, role TEXT NOT NULL, name TEXT NOT NULL, "
        "is_active INTEGER NOT NULL DEFAULT 1)"
    )
    accounts = [
        ("admin", "admin123", "Admin", "Admin Master"),
        ("cashier", "cashier123", "Cashier", "Cashier Lead"),
        ("kitchen", "kitchen123", "Staff_Kitchen", "Kitchen Supervisor"),
        ("logistics", "logistics123", "Staff_Logistics", "Logistics Officer"),
        ("utilities", "utilities123", "Staff_Utilities", "Utilities Attendant"),
    ]
    for username, password, role, name in accounts:
        connection.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role, name) VALUES (?, ?, ?, ?)",
            (username, _hash_password(password), role, name),
        )
    connection.commit()
    connection.close()


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    user = connection.execute(
        "SELECT username, password_hash, role, name FROM users "
        "WHERE username = ? AND is_active = 1", (username,)
    ).fetchone()
    connection.close()
    if not user or not _verify_password(password, user["password_hash"]):
        return jsonify({"ok": False, "message": "Invalid credentials."}), 401
    return jsonify({"ok": True, "name": user["name"], "role": user["role"]})


def start_server(writable_directory):
    global database_path
    database_path = Path(writable_directory) / "hotel_service.db"
    _initialize_database()
    thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=8765, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
