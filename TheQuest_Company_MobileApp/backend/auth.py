"""
Authentication and Access Control for The Quest Mobile App.
Supports:
- PBKDF2 SHA-256 password hashing and verification
- 3-strike brute-force defense with strict 60-second lockout timer
- Role-based session authorization (Admin, Cashier, Kitchen, Logistics, Utilities)
- Encrypted event logging
"""

import time
import hashlib
import hmac
import secrets
import re
from typing import Tuple, Optional, Dict, Any

from .db import query_db, execute_db
from .logger import log_auth_event

# In-memory tracking for failed attempts and lockout timers: {key: {"count": int, "until": float}}
_LOCKOUT_CACHE: Dict[str, Dict[str, Any]] = {}


def hash_password(password: str) -> str:
    """Generate salted PBKDF2-HMAC-SHA256 password hash."""
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${hashed.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash or legacy string."""
    try:
        if not stored_hash:
            return False
        if "$" in stored_hash:
            salt_hex, hash_hex = stored_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
            for iters in [100_000, 600_000]:
                test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
                if hmac.compare_digest(test, expected):
                    return True
            return False
        return hmac.compare_digest(password, stored_hash)
    except Exception:
        return False


def get_lockout_status(key: str) -> Tuple[bool, int]:
    """Check if the client or username is currently under lockout."""
    state = _LOCKOUT_CACHE.get(key)
    if not state:
        return False, 0
    now = time.time()
    until = state.get("until", 0)
    if now < until:
        return True, int(until - now)
    return False, 0


def record_failed_attempt(key: str, username: str) -> Tuple[int, int]:
    """
    Record a failed login. Returns (attempts_count, lockout_seconds).
    If attempts >= 3, applies a 60-second lockout.
    """
    now = time.time()
    state = _LOCKOUT_CACHE.setdefault(key, {"count": 0, "until": 0})

    # If previous lockout expired, reset count
    if state["until"] > 0 and now >= state["until"]:
        state["count"] = 0
        state["until"] = 0

    state["count"] += 1
    log_auth_event(
        event_type="LOGIN_FAILED",
        username=username,
        role="Unknown",
        status="FAILURE",
        details=f"Failed attempt {state['count']}/3 from mobile client"
    )

    if state["count"] >= 3:
        state["until"] = now + 60
        state["count"] = 0
        log_auth_event(
            event_type="ACCOUNT_LOCKOUT",
            username=username,
            role="Unknown",
            status="LOCKOUT",
            details="Mobile account lockout triggered: 60s cooldown enforced."
        )
        return 3, 60

    return state["count"], 0


def clear_failed_attempts(key: str):
    """Reset attempt counter upon successful authentication."""
    if key in _LOCKOUT_CACHE:
        del _LOCKOUT_CACHE[key]


def authenticate_user(username: str, password: str, client_ip: str = "127.0.0.1") -> Tuple[Optional[dict], Optional[str], int]:
    """
    Authenticate employee.
    Returns (user_data_dict, error_message, lockout_seconds).
    """
    lock_key = f"{client_ip}:{username.strip().lower()}"
    is_locked, remaining = get_lockout_status(lock_key)
    if is_locked:
        return None, f"System Locked. Too many failed attempts. Try again in {remaining}s.", remaining

    username = username.strip()
    if not username or not password:
        return None, "Please provide both username and password.", 0

    user = query_db(
        "SELECT id, username, password_hash, role, name, phone, email, image_path, is_active FROM users WHERE username = ?",
        (username,),
        one=True
    )

    if not user:
        attempts, lockout = record_failed_attempt(lock_key, username)
        if lockout > 0:
            return None, f"System Locked. Too many failed attempts. Wait 60s.", lockout
        return None, f"Invalid credentials. {3 - attempts} attempt(s) remaining.", 0

    if not user.get("is_active", 1):
        return None, "This staff account is deactivated. Contact Administrator.", 0

    if not verify_password(password, user["password_hash"]):
        attempts, lockout = record_failed_attempt(lock_key, username)
        if lockout > 0:
            return None, f"System Locked. Too many failed attempts. Wait 60s.", lockout
        return None, f"Invalid credentials. {3 - attempts} attempt(s) remaining.", 0

    # Authentication Success
    clear_failed_attempts(lock_key)
    log_auth_event(
        event_type="LOGIN_SUCCESS",
        username=username,
        role=user["role"],
        status="SUCCESS",
        details=f"Mobile authentication successful for {user['name']}"
    )
    return user, None, 0


def register_staff_account(username: str, password: str, role: str, name: str, phone: str = "", email: str = "") -> Tuple[bool, str]:
    """Register a new employee with secure hashing and assigned role."""
    username = username.strip()
    name = name.strip()
    if not username or not password or not role or not name:
        return False, "Username, password, role, and full name are required."

    allowed_roles = {"Admin", "Cashier", "Staff_Kitchen", "Staff_Logistics", "Staff_Utilities"}
    if role not in allowed_roles:
        return False, f"Invalid role. Must be one of: {', '.join(allowed_roles)}"

    existing = query_db("SELECT id FROM users WHERE username = ?", (username,), one=True)
    if existing:
        return False, f"Username '{username}' is already in use."

    pwd_hash = hash_password(password)
    default_avatar = "assets/imgs/employees/m/1.jpg" if "Admin" in role else "assets/imgs/employees/f/2.jpg"

    try:
        user_id = execute_db("""
            INSERT INTO users (username, password_hash, role, name, phone, email, image_path, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (username, pwd_hash, role, name, phone, email, default_avatar))

        log_auth_event(
            event_type="STAFF_REGISTERED",
            username=username,
            role=role,
            status="SUCCESS",
            details=f"New employee registered: {name} (ID: {user_id})"
        )
        return True, "Employee registered successfully."
    except Exception as e:
        return False, f"Database error during registration: {e}"
