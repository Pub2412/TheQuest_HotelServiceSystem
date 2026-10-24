"""
Staff Operations Services for The Quest Mobile App.
Provides specialized business logic for:
1. Kitchen: In-room food orders & ingredient stock management
2. Logistics: Deliveries with passcode verification ('QUEST-LOG-2026')
3. Utilities: Room servicing & housekeeping (with strict policy hiding vacant suites)
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .db import query_db, execute_db, get_connection

LOGISTICS_AUTH_CODE = "QUEST-LOG-2026"


# ==============================================================================
# 1. KITCHEN OPERATIONS
# ==============================================================================

def get_kitchen_orders() -> List[Dict[str, Any]]:
    """Retrieve food service requests and in-room dining orders."""
    sql = """
        SELECT sr.id, sr.request_type, sr.details, sr.status, sr.date_created,
               rm.room_number, c.name as customer_name, c.mobile_number
        FROM service_requests sr
        LEFT JOIN rooms rm ON sr.room_id = rm.id
        LEFT JOIN customers c ON sr.customer_id = c.id
        WHERE sr.request_type = 'Food Delivery' OR sr.request_type LIKE '%Food%'
        ORDER BY (sr.status = 'Processing') DESC, sr.date_created DESC
    """
    return query_db(sql)


def update_kitchen_order_status(request_id: int, new_status: str, staff_name: str = "Kitchen Staff") -> Tuple[bool, str]:
    """Transition food order status (e.g. Processing -> Ready for Delivery -> Complete)."""
    allowed = {"Processing", "Ready for Delivery", "Complete", "Canceled"}
    if new_status not in allowed:
        return False, f"Invalid status: {new_status}"

    execute_db("UPDATE service_requests SET status = ? WHERE id = ?", (new_status, request_id))
    return True, f"Order #{request_id} updated to '{new_status}'."


def get_kitchen_inventory() -> List[Dict[str, Any]]:
    """Retrieve kitchen ingredients with low-stock status."""
    items = query_db("""
        SELECT id, item_name, category, quantity, low_stock_threshold, unit, cost_per_unit
        FROM inventory
        WHERE category = 'Kitchen'
        ORDER BY (quantity <= low_stock_threshold) DESC, item_name ASC
    """)
    for it in items:
        it["is_low"] = it["quantity"] <= it["low_stock_threshold"]
    return items


# ==============================================================================
# 2. LOGISTICS OPERATIONS (Passcode: QUEST-LOG-2026)
# ==============================================================================

def get_logistics_deliveries(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve categorized shipments: 'Will be Shipped', 'On the Way', 'Near Receive', etc."""
    sql = "SELECT id, description, status, logistics_code, date_updated FROM deliveries"
    args = []
    if status_filter and status_filter != "All":
        sql += " WHERE status = ?"
        args.append(status_filter)
    sql += " ORDER BY id DESC"
    return query_db(sql, args)


def update_delivery_status(delivery_id: int, new_status: str, passcode: str = "", staff_name: str = "Logistics") -> Tuple[bool, str]:
    """
    Update delivery progression.
    Passcode 'QUEST-LOG-2026' is strictly required for completing or canceling shipments.
    """
    requires_code = new_status in {"Completed", "Canceled"}
    if requires_code:
        if passcode.strip() != LOGISTICS_AUTH_CODE:
            return False, "Authorization Denied: Incorrect Logistics Passcode."

    execute_db("""
        UPDATE deliveries
        SET status = ?, date_updated = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_status, delivery_id))

    return True, f"Shipment #{delivery_id} marked as '{new_status}'."


def add_logistics_delivery(description: str, logistics_code: str, status: str = "Will be Shipped") -> int:
    """Register incoming freight shipment."""
    return execute_db("""
        INSERT INTO deliveries (description, logistics_code, status, date_updated)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (description, logistics_code, status))


# ==============================================================================
# 3. UTILITIES & HOUSEKEEPING OPERATIONS (Strictly hides empty/vacant rooms)
# ==============================================================================

def get_rooms_needing_service() -> List[Dict[str, Any]]:
    """
    Retrieve rooms requiring housekeeping.
    Policy enforcement: Empty/Vacant rooms are strictly excluded from Utilities visibility.
    """
    sql = """
        SELECT rm.id, rm.room_number, rm.type, rm.status, rm.price_per_night, rm.packs,
               c.name as current_guest, r.id as res_id
        FROM rooms rm
        LEFT JOIN reservations r ON rm.id = r.room_id AND r.status = 'Checked In'
        LEFT JOIN customers c ON r.customer_id = c.id
        WHERE rm.status = 'Needs Service'
        ORDER BY rm.room_number ASC
    """
    return query_db(sql)


def get_utility_service_requests() -> List[Dict[str, Any]]:
    """Retrieve housekeeping and utility maintenance tasks."""
    sql = """
        SELECT sr.id, sr.request_type, sr.details, sr.status, sr.date_created,
               rm.room_number, c.name as customer_name
        FROM service_requests sr
        LEFT JOIN rooms rm ON sr.room_id = rm.id
        LEFT JOIN customers c ON sr.customer_id = c.id
        WHERE sr.request_type = 'Room Service' OR sr.request_type LIKE '%Clean%' OR sr.request_type LIKE '%Utility%'
        ORDER BY (sr.status = 'Processing') DESC, sr.date_created DESC
    """
    return query_db(sql)


def mark_room_cleaned_and_ready(room_id: int, staff_name: str = "Housekeeping Attendant") -> Tuple[bool, str]:
    """
    Completes housekeeping for a room:
    - Sets room status to 'Vacant'
    - Closes related pending service requests
    """
    room = query_db("SELECT id, room_number, status FROM rooms WHERE id = ?", (room_id,), one=True)
    if not room:
        return False, "Room not found."

    with get_connection() as conn:
        conn.execute("UPDATE rooms SET status = 'Vacant', is_occupied = 0, is_reserved = 0 WHERE id = ?", (room_id,))
        # Close any cleaning service requests
        conn.execute("""
            UPDATE service_requests
            SET status = 'Complete'
            WHERE room_id = ? AND status = 'Processing'
        """, (room_id,))

    return True, f"Suite {room['room_number']} cleaned, sanitized, and set to VACANT."


def update_utility_task_status(task_id: int, new_status: str, staff_name: str = "Housekeeping") -> Tuple[bool, str]:
    """Update maintenance or cleaning ticket status."""
    allowed = {"Processing", "Complete", "Canceled"}
    if new_status not in allowed:
        return False, f"Invalid status: {new_status}"

    execute_db("UPDATE service_requests SET status = ? WHERE id = ?", (new_status, task_id))
    return True, f"Task #{task_id} updated to '{new_status}'."
