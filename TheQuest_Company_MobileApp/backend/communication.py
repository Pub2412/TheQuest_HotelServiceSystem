"""
Internal Staff Communication and Dispatch Services for The Quest Mobile App.
Includes:
- Company bulletin announcements
- Direct & role-based staff messaging
- Softphone dispatch directory
"""

from typing import List, Dict, Any, Optional

from .db import query_db, execute_db


def get_bulletin_announcements() -> List[Dict[str, Any]]:
    """Retrieve internal bulletin announcements with author profile."""
    sql = """
        SELECT b.id, b.title, b.content, b.timestamp,
               u.name as author_name, u.role as author_role, u.image_path as author_image
        FROM bulletin b
        LEFT JOIN users u ON b.author_id = u.id
        ORDER BY b.timestamp DESC
    """
    return query_db(sql)


def post_bulletin_announcement(author_id: int, title: str, content: str) -> int:
    """Publish a new announcement to the internal company board."""
    return execute_db("""
        INSERT INTO bulletin (author_id, title, content, timestamp)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (author_id, title, content))


def get_user_inbox_messages(user_id: int, user_role: str) -> List[Dict[str, Any]]:
    """Retrieve staff messages sent directly to this user or broadcast to their operational role."""
    sql = """
        SELECT m.id, m.content, m.timestamp, m.sender_id, m.receiver_id, m.receiver_role,
               u.name as sender_name, u.role as sender_role, u.image_path as sender_image
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.receiver_id = ? OR m.receiver_role = ? OR m.receiver_role = 'All' OR m.receiver_id IS NULL
        ORDER BY m.timestamp DESC
    """
    return query_db(sql, (user_id, user_role))


def send_staff_message(sender_id: int, content: str, receiver_id: Optional[int] = None, receiver_role: Optional[str] = None) -> int:
    """Dispatch a staff memo or broadcast message."""
    return execute_db("""
        INSERT INTO messages (sender_id, receiver_id, receiver_role, content, timestamp)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (sender_id, receiver_id, receiver_role, content))


def get_softphone_directory(exclude_user_id: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve phone numbers for one-tap softphone simulated calling:
    - Colleagues & Staff
    - Active Checked-In Guests
    """
    staff_sql = """
        SELECT id, name, role, phone, email, image_path
        FROM users
        WHERE is_active = 1
    """
    args = []
    if exclude_user_id:
        staff_sql += " AND id != ?"
        args.append(exclude_user_id)
    staff_sql += " ORDER BY role ASC, name ASC"

    staff_contacts = query_db(staff_sql, args)

    guest_sql = """
        SELECT c.id, c.name, 'Checked-In Guest' as role, c.mobile_number as phone, c.email, c.image_path,
               rm.room_number
        FROM reservations r
        JOIN customers c ON r.customer_id = c.id
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.status = 'Checked In'
        ORDER BY rm.room_number ASC
    """
    guest_contacts = query_db(guest_sql)

    return {
        "staff": staff_contacts,
        "guests": guest_contacts
    }
