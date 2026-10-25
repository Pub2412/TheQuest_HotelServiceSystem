"""
Authentication and security management for The Quest Hotel Customer Website.
Implements:
- Password hashing & verification using PBKDF2 SHA-256 (matches seed_data.py)
- 3-strike login lockout with 60-second timer
- Multi-factor login (Email, Mobile, Google, Facebook)
- Registration with welcome bonus
- Forgot Password reset
- Profile RUD and social linking
"""

import time
import secrets
import hashlib
import hmac
import uuid
from pathlib import Path
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from .db import get_connection, get_customer_by_id, get_customer_by_identifier

# In-memory lockout tracker: { identifier_or_ip: {"attempts": int, "lockout_until": float} }
LOGIN_ATTEMPTS = {}
LOCKOUT_DURATION_SECONDS = 60
MAX_ATTEMPTS = 3
PROFILE_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
PROFILE_IMAGE_MAX_BYTES = 5 * 1024 * 1024

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a 16-byte random salt."""
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${hashed.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash or fallback plain string."""
    try:
        if not stored_hash:
            return False
        if "$" in stored_hash:
            salt_hex, hash_hex = stored_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)
            for iters in [100_000, 600_000]:
                test_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
                if hmac.compare_digest(test_hash, expected_hash):
                    return True
            return False
        return hmac.compare_digest(password, stored_hash)
    except Exception:
        return False

def check_lockout(key: str) -> Tuple[bool, int]:
    """Check if key (IP or identifier) is locked out. Returns (is_locked, remaining_seconds)."""
    now = time.time()
    record = LOGIN_ATTEMPTS.get(key)
    if not record:
        return False, 0

    lockout_until = record.get("lockout_until", 0)
    if now < lockout_until:
        return True, int(lockout_until - now)

    # Lockout expired, reset attempts if lockout has passed
    if lockout_until > 0 and now >= lockout_until:
        LOGIN_ATTEMPTS[key] = {"attempts": 0, "lockout_until": 0}

    return False, 0

def record_failed_attempt(key: str) -> Tuple[bool, int, int]:
    """
    Record a failed attempt.
    Returns (is_now_locked, remaining_seconds, current_attempts).
    """
    now = time.time()
    record = LOGIN_ATTEMPTS.get(key, {"attempts": 0, "lockout_until": 0})
    
    # If previously locked and time has elapsed, reset counter
    if record["lockout_until"] > 0 and now >= record["lockout_until"]:
        record["attempts"] = 0
        record["lockout_until"] = 0

    record["attempts"] += 1

    if record["attempts"] >= MAX_ATTEMPTS:
        record["lockout_until"] = now + LOCKOUT_DURATION_SECONDS
        LOGIN_ATTEMPTS[key] = record
        return True, LOCKOUT_DURATION_SECONDS, record["attempts"]

    LOGIN_ATTEMPTS[key] = record
    return False, 0, record["attempts"]

def record_successful_attempt(key: str):
    """Clear failed attempts on successful login."""
    if key in LOGIN_ATTEMPTS:
        del LOGIN_ATTEMPTS[key]

def authenticate_customer(identifier: str, password: str, client_ip: str = "") -> Tuple[bool, Optional[dict], str]:
    """
    Authenticate by email or mobile number with lockout enforcement.
    Returns (success, customer_dict, message).
    """
    lock_key = client_ip or identifier
    is_locked, secs_left = check_lockout(lock_key)
    if is_locked:
        return False, None, f"Too many failed attempts. Security lockout active. Please wait {secs_left} seconds."

    customer = get_customer_by_identifier(identifier)
    if not customer:
        is_now_locked, lock_secs, att = record_failed_attempt(lock_key)
        if is_now_locked:
            return False, None, f"Account locked for 60 seconds due to 3 failed attempts."
        remaining = MAX_ATTEMPTS - att
        return False, None, f"Invalid credentials. {remaining} attempt(s) remaining before 1-minute lockout."

    if not verify_password(password, customer.get("password_hash") or ""):
        is_now_locked, lock_secs, att = record_failed_attempt(lock_key)
        if is_now_locked:
            return False, None, f"Account locked for 60 seconds due to 3 failed attempts."
        remaining = MAX_ATTEMPTS - att
        return False, None, f"Incorrect password. {remaining} attempt(s) remaining before 1-minute lockout."

    # Login succeeded
    record_successful_attempt(lock_key)
    return True, customer, "Login successful."

def validate_profile_image(uploaded_file) -> Optional[str]:
    """Validate an uploaded profile image before it is stored."""
    if not uploaded_file or not uploaded_file.filename:
        return None

    filename = secure_filename(uploaded_file.filename)
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in PROFILE_IMAGE_EXTENSIONS:
        return "Profile picture must be JPG, JPEG, PNG, or WEBP."
    if uploaded_file.mimetype not in {"image/jpeg", "image/png", "image/webp"}:
        return "The selected profile picture is not a supported image type."

    uploaded_file.stream.seek(0, 2)
    size = uploaded_file.stream.tell()
    uploaded_file.stream.seek(0)
    if size > PROFILE_IMAGE_MAX_BYTES:
        return "Profile picture must be 5 MB or smaller."
    return None


def store_profile_image(uploaded_file, customer_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Store a validated profile image and return its database path or an error."""
    error = validate_profile_image(uploaded_file)
    if error:
        return None, error
    if not uploaded_file or not uploaded_file.filename:
        return None, None

    extension = Path(secure_filename(uploaded_file.filename)).suffix.lower()
    upload_dir = Path(__file__).resolve().parents[2] / "assets" / "imgs" / "customers" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"customer_{customer_id}_{uuid.uuid4().hex}{extension}"
    uploaded_file.save(str(upload_dir / filename))
    return f"assets/imgs/customers/uploads/{filename}", None


def register_customer(name: str, email: str, mobile_number: str, password: str,
                      profile_image=None) -> Tuple[bool, Optional[dict], str]:
    """Register a new customer with 100 initial welcome loyalty points."""
    if not name or not password or (not email and not mobile_number):
        return False, None, "Please provide your name, password, and at least an email or mobile number."
    image_error = validate_profile_image(profile_image)
    if image_error:
        return False, None, image_error

    conn = get_connection()
    c = conn.cursor()

    # Check uniqueness
    if email:
        c.execute("SELECT id FROM customers WHERE LOWER(email) = LOWER(?)", (email,))
        if c.fetchone():
            conn.close()
            return False, None, "An account with this email address already exists."

    if mobile_number:
        clean_phone = mobile_number.replace(" ", "")
        c.execute("SELECT id FROM customers WHERE REPLACE(mobile_number, ' ', '') = ?", (clean_phone,))
        if c.fetchone():
            conn.close()
            return False, None, "An account with this mobile number already exists."

    pwd_hash = hash_password(password)
    # Default avatar based on customer count (alternating avatars from assets)
    avatar = "assets/imgs/customers/f/1.jpg"

    try:
        c.execute("""
            INSERT INTO customers (name, email, mobile_number, password_hash, loyalty_points, image_path)
            VALUES (?, ?, ?, ?, 100, ?)
        """, (name, email, mobile_number, pwd_hash, avatar))
        new_id = c.lastrowid
        image_path, image_error = store_profile_image(profile_image, new_id)
        if image_error:
            conn.rollback()
            conn.close()
            return False, None, image_error
        if image_path:
            c.execute("UPDATE customers SET image_path = ? WHERE id = ?", (image_path, new_id))
        conn.commit()

        c.execute("SELECT * FROM customers WHERE id = ?", (new_id,))
        new_customer = dict(c.fetchone())
        conn.close()
        return True, new_customer, "Registration successful! Welcome to The Quest. You received 100 welcome loyalty points."
    except Exception as e:
        conn.close()
        return False, None, f"Registration failed: {str(e)}"

def reset_password(identifier: str, new_password: str) -> Tuple[bool, str]:
    """Reset customer password by email or mobile identifier."""
    customer = get_customer_by_identifier(identifier)
    if not customer:
        return False, "No customer account found with that email or mobile number."

    new_hash = hash_password(new_password)
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE customers SET password_hash = ? WHERE id = ?", (new_hash, customer["id"]))
    conn.commit()
    conn.close()
    return True, "Your password has been successfully reset. You may now sign in."

def social_login(provider: str, social_id: str, email: str, name: str) -> Tuple[bool, Optional[dict], str]:
    """
    Handle simulated OAuth login (Google or Facebook).
    If customer with social_id or email exists, log them in.
    Otherwise create a new customer record linked to this provider.
    """
    conn = get_connection()
    c = conn.cursor()

    col = "google_id" if provider.lower() == "google" else "facebook_id"

    # 1. Match by social_id
    c.execute(f"SELECT * FROM customers WHERE {col} = ?", (social_id,))
    row = c.fetchone()
    if row:
        conn.close()
        return True, dict(row), f"Welcome back, {row['name']}!"

    # 2. Match by email
    if email:
        c.execute("SELECT * FROM customers WHERE LOWER(email) = LOWER(?)", (email,))
        row = c.fetchone()
        if row:
            # Link social ID to existing account
            c.execute(f"UPDATE customers SET {col} = ? WHERE id = ?", (social_id, row["id"]))
            conn.commit()
            updated = dict(row)
            updated[col] = social_id
            conn.close()
            return True, updated, f"Linked your {provider} account. Welcome back, {row['name']}!"

    # 3. Create new customer with welcome points
    default_phone = "+63 900 000 0000"
    avatar = "assets/imgs/customers/f/2.jpg"
    c.execute(f"""
        INSERT INTO customers (name, email, mobile_number, loyalty_points, image_path, {col})
        VALUES (?, ?, ?, 100, ?, ?)
    """, (name, email, default_phone, avatar, social_id))
    new_id = c.lastrowid
    conn.commit()

    c.execute("SELECT * FROM customers WHERE id = ?", (new_id,))
    new_user = dict(c.fetchone())
    conn.close()
    return True, new_user, f"Welcome to The Quest! Your {provider} account has been registered with 100 bonus loyalty points."
