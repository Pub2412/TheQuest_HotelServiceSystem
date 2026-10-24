"""
Front Desk Cashier Operations and Reservation Services for The Quest Mobile App.
Manages bookings, check-in, check-out billing, room transfers, and room statuses.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from .db import query_db, execute_db, get_connection


def get_all_reservations(status_filter: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve reservations with joined room and customer information."""
    sql = """
        SELECT r.id, r.check_in_date, r.check_out_date, r.status,
               rm.id as room_id, rm.room_number, rm.type as room_type, rm.price_per_night,
               c.id as customer_id, c.name as customer_name, c.mobile_number, c.email, c.loyalty_points
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        JOIN customers c ON r.customer_id = c.id
    """
    conditions = []
    args = []

    if status_filter and status_filter != "All":
        conditions.append("r.status = ?")
        args.append(status_filter)

    if search:
        conditions.append("(c.name LIKE ? OR rm.room_number LIKE ? OR c.mobile_number LIKE ?)")
        like = f"%{search}%"
        args.extend([like, like, like])

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY r.id DESC"
    return query_db(sql, args)


def get_available_rooms() -> List[Dict[str, Any]]:
    """Retrieve rooms that are Vacant and ready for booking."""
    return query_db("SELECT id, room_number, type, price_per_night, packs FROM rooms WHERE status = 'Vacant' ORDER BY room_number ASC")


def create_new_reservation(customer_id: int, room_id: int, check_in_str: str, check_out_str: str, immediate_checkin: bool = False, cashier_name: str = "Front Desk") -> Tuple[bool, str, Optional[int]]:
    """Create a new reservation record, with option for immediate check-in."""
    room = query_db("SELECT id, room_number, price_per_night, status FROM rooms WHERE id = ?", (room_id,), one=True)
    if not room:
        return False, "Selected suite was not found.", None

    if room["status"] != "Vacant":
        return False, f"Room {room['room_number']} is currently {room['status']} and cannot be booked.", None

    # Calculate days
    try:
        ci_date = datetime.strptime(check_in_str[:10], "%Y-%m-%d").date()
        co_date = datetime.strptime(check_out_str[:10], "%Y-%m-%d").date()
        nights = max(1, (co_date - ci_date).days)
    except Exception:
        nights = 1

    total_amount = nights * room["price_per_night"]
    initial_status = "Checked In" if immediate_checkin else "Pending"

    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO reservations (customer_id, room_id, check_in_date, check_out_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, room_id, check_in_str, check_out_str, initial_status))
        res_id = cur.lastrowid

        if immediate_checkin:
            conn.execute("UPDATE rooms SET status = 'Occupied', is_occupied = 1, is_reserved = 0 WHERE id = ?", (room_id,))
            conn.execute("""
                INSERT INTO transactions (type, amount, description, customer_id, date_recorded)
                VALUES ('Revenue', ?, ?, ?, CURRENT_TIMESTAMP)
            """, (total_amount, f"Walk-In Check-In: Room {room['room_number']} ({nights} nights) by {cashier_name}", customer_id))
        else:
            conn.execute("UPDATE rooms SET status = 'Reserved', is_reserved = 1, is_occupied = 0 WHERE id = ?", (room_id,))

    return True, f"Reservation #{res_id} created successfully.", res_id


def check_in_guest(reservation_id: int, cashier_name: str = "Cashier") -> Tuple[bool, str]:
    """Execute guest check-in: flips room to Occupied and logs revenue."""
    res = query_db("""
        SELECT r.id, r.customer_id, r.room_id, r.check_in_date, r.check_out_date, r.status,
               rm.room_number, rm.price_per_night
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        WHERE r.id = ?
    """, (reservation_id,), one=True)

    if not res:
        return False, "Reservation not found."

    if res["status"] == "Checked In":
        return False, "Guest is already checked in."

    try:
        ci_date = datetime.strptime(str(res["check_in_date"])[:10], "%Y-%m-%d").date()
        co_date = datetime.strptime(str(res["check_out_date"])[:10], "%Y-%m-%d").date()
        nights = max(1, (co_date - ci_date).days)
    except Exception:
        nights = 1

    total_amount = nights * float(res["price_per_night"])

    with get_connection() as conn:
        conn.execute("UPDATE reservations SET status = 'Checked In' WHERE id = ?", (reservation_id,))
        conn.execute("UPDATE rooms SET status = 'Occupied', is_occupied = 1, is_reserved = 0 WHERE id = ?", (res["room_id"],))
        conn.execute("""
            INSERT INTO transactions (type, amount, description, customer_id, date_recorded)
            VALUES ('Revenue', ?, ?, ?, CURRENT_TIMESTAMP)
        """, (total_amount, f"Check-In Room {res['room_number']} ({nights} nights) by {cashier_name}", res["customer_id"]))

    return True, f"Room {res['room_number']} checked in successfully."


def check_out_guest(reservation_id: int, cashier_name: str = "Cashier") -> Tuple[bool, str, Dict[str, Any]]:
    """
    Execute guest check-out:
    - Marks reservation Checked Out
    - Sets room status to Needs Service
    - Awards loyalty points
    """
    res = query_db("""
        SELECT r.id, r.customer_id, r.room_id, r.check_in_date, r.check_out_date, r.status,
               rm.room_number, rm.price_per_night, c.name as customer_name, c.loyalty_points
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        JOIN customers c ON r.customer_id = c.id
        WHERE r.id = ?
    """, (reservation_id,), one=True)

    if not res:
        return False, "Reservation record not found.", {}

    if res["status"] != "Checked In":
        return False, f"Cannot check out reservation in '{res['status']}' state.", {}

    try:
        ci_date = datetime.strptime(str(res["check_in_date"])[:10], "%Y-%m-%d").date()
        co_date = datetime.strptime(str(res["check_out_date"])[:10], "%Y-%m-%d").date()
        nights = max(1, (co_date - ci_date).days)
    except Exception:
        nights = 1

    room_total = nights * float(res["price_per_night"])
    # Award loyalty points (1 point per 100 PHP)
    earned_points = int(room_total // 100)

    with get_connection() as conn:
        conn.execute("UPDATE reservations SET status = 'Checked Out' WHERE id = ?", (reservation_id,))
        # Room now needs cleaning by utilities staff!
        conn.execute("UPDATE rooms SET status = 'Needs Service', is_occupied = 0, is_reserved = 0 WHERE id = ?", (res["room_id"],))
        conn.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (earned_points, res["customer_id"]))

    summary = {
        "reservation_id": reservation_id,
        "room_number": res["room_number"],
        "customer_name": res["customer_name"],
        "nights": nights,
        "total_amount": room_total,
        "earned_points": earned_points
    }
    return True, f"Check-out complete for Suite {res['room_number']}. Room transferred to Housekeeping queue.", summary


def change_guest_room(reservation_id: int, new_room_id: int, cashier_name: str = "Cashier") -> Tuple[bool, str]:
    """Transfer an active or pending reservation to another vacant room."""
    res = query_db("SELECT id, room_id, status FROM reservations WHERE id = ?", (reservation_id,), one=True)
    if not res:
        return False, "Reservation not found."

    old_room_id = res["room_id"]
    new_room = query_db("SELECT id, room_number, status FROM rooms WHERE id = ?", (new_room_id,), one=True)
    if not new_room or new_room["status"] != "Vacant":
        return False, "Target room is not vacant."

    with get_connection() as conn:
        # Move reservation to new room
        conn.execute("UPDATE reservations SET room_id = ? WHERE id = ?", (new_room_id, reservation_id))

        if res["status"] == "Checked In":
            # Free old room for cleaning
            conn.execute("UPDATE rooms SET status = 'Needs Service', is_occupied = 0, is_reserved = 0 WHERE id = ?", (old_room_id,))
            # Occupy new room
            conn.execute("UPDATE rooms SET status = 'Occupied', is_occupied = 1, is_reserved = 0 WHERE id = ?", (new_room_id,))
        else:
            # Free old room to vacant
            conn.execute("UPDATE rooms SET status = 'Vacant', is_occupied = 0, is_reserved = 0 WHERE id = ?", (old_room_id,))
            conn.execute("UPDATE rooms SET status = 'Reserved', is_occupied = 0, is_reserved = 1 WHERE id = ?", (new_room_id,))

    return True, f"Room transfer successful. Guest reassigned to Room {new_room['room_number']}."


def cancel_guest_reservation(reservation_id: int, cashier_name: str = "Cashier") -> Tuple[bool, str]:
    """Cancel a booking and free up the allocated room."""
    res = query_db("SELECT id, room_id, status FROM reservations WHERE id = ?", (reservation_id,), one=True)
    if not res:
        return False, "Reservation not found."

    with get_connection() as conn:
        conn.execute("UPDATE reservations SET status = 'Canceled' WHERE id = ?", (reservation_id,))
        conn.execute("UPDATE rooms SET status = 'Vacant', is_occupied = 0, is_reserved = 0 WHERE id = ?", (res["room_id"],))

    return True, "Reservation has been canceled and room released."


def create_quick_walkin_guest(name: str, email: str, phone: str) -> Tuple[bool, str, Optional[int]]:
    """Instantly enroll a walk-in guest into customers table."""
    name = name.strip()
    if not name:
        return False, "Guest name is required.", None

    existing = query_db("SELECT id FROM customers WHERE mobile_number = ? OR email = ?", (phone, email), one=True)
    if existing:
        return True, "Existing customer selected.", existing["id"]

    cust_id = execute_db("""
        INSERT INTO customers (name, email, mobile_number, loyalty_points, image_path)
        VALUES (?, ?, ?, 100, 'assets/imgs/customers/f/1.jpg')
    """, (name, email, phone))
    return True, f"Guest {name} registered with 100 welcome bonus points.", cust_id
