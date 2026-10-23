"""
Database connector and query helper for The Quest Hotel Customer Website.
Connects dynamically and portably to hotel_service.db in the database/ directory.
"""

import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

def get_database_path() -> Path:
    """Dynamically resolve the path to hotel_service.db regardless of where the app is launched."""
    # Strategy 1: Relative to this file (backend/db.py -> TheQuest_Customer_Website -> FinalProject_Hotel_Service -> database)
    candidate1 = Path(__file__).resolve().parents[2] / "database" / "hotel_service.db"
    if candidate1.exists():
        return candidate1

    # Strategy 2: Relative to current working directory
    cwd = Path.cwd()
    candidate2 = cwd / "database" / "hotel_service.db"
    if candidate2.exists():
        return candidate2

    candidate3 = cwd.parent / "database" / "hotel_service.db"
    if candidate3.exists():
        return candidate3

    # Fallback to candidate1 path (creates if setup_db is run)
    return candidate1

DB_PATH = get_database_path()

def get_connection():
    """Create and return a SQLite connection with Row factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_customer_tables():
    """Ensure additional auxiliary tables exist without altering existing schema."""
    conn = get_connection()
    c = conn.cursor()

    # Redeemed Rewards Table (for customer loyalty reward vouchers)
    c.execute("""
    CREATE TABLE IF NOT EXISTS redeemed_rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        reward_id INTEGER NOT NULL,
        reward_name TEXT NOT NULL,
        points_spent INTEGER NOT NULL,
        voucher_code TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'Active', -- Active, Used, Expired
        date_redeemed DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(reward_id) REFERENCES loyalty_rewards(id)
    )
    """)

    # Customer Inquiries & Chat Messages (for Concierge & Front Desk desk inquiries)
    c.execute("""
    CREATE TABLE IF NOT EXISTS customer_inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        room_id INTEGER,
        department TEXT DEFAULT 'Front Desk', -- Front Desk, Concierge, Housekeeping, Room Service
        sender_type TEXT DEFAULT 'Customer',  -- Customer, Staff
        message TEXT NOT NULL,
        response TEXT,
        status TEXT DEFAULT 'Pending',        -- Pending, Answered, Resolved
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id),
        FOREIGN KEY(room_id) REFERENCES rooms(id)
    )
    """)

    conn.commit()
    conn.close()

def get_customer_by_id(customer_id: int):
    """Retrieve full customer record by primary key."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_customer_by_identifier(identifier: str):
    """Retrieve customer by email OR mobile number."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM customers 
        WHERE LOWER(email) = LOWER(?) OR REPLACE(mobile_number, ' ', '') = REPLACE(?, ' ', '')
    """, (identifier, identifier))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_active_stay(customer_id: int):
    """
    Check if a customer has an active 'Checked In' reservation.
    Returns stay details including room number, room type, dates, and remaining duration.
    """
    if not customer_id:
        return None

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT res.id AS reservation_id, res.check_in_date, res.check_out_date, res.status,
               r.id AS room_id, r.room_number, r.type AS room_type, r.price_per_night, r.packs
        FROM reservations res
        JOIN rooms r ON res.room_id = r.id
        WHERE res.customer_id = ? AND res.status = 'Checked In'
        ORDER BY res.id DESC
        LIMIT 1
    """, (customer_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    stay = dict(row)
    # Calculate stay countdown
    # Standard check-out is at 12:00 PM (noon) on the check_out_date
    now = datetime.now()
    try:
        co_date = datetime.strptime(stay["check_out_date"], "%Y-%m-%d").replace(hour=12, minute=0, second=0)
    except Exception:
        co_date = now + timedelta(days=1)

    time_left = co_date - now
    total_seconds = int(time_left.total_seconds())

    if total_seconds > 0:
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        is_overdue = False
        status_text = f"{days}d {hours}h {minutes}m left"
    else:
        # Overdue or checkout due now
        days = 0
        hours = 0
        minutes = 0
        seconds = 0
        is_overdue = True
        status_text = "Checkout Due / Overdue"

    stay["countdown"] = {
        "total_seconds": max(0, total_seconds),
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "is_overdue": is_overdue,
        "status_text": status_text,
        "target_iso": co_date.isoformat()
    }

    return stay
