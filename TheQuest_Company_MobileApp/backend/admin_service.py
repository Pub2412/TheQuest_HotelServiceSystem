"""
Admin Business Logic and Executive Reporting for The Quest Mobile App.
Provides metrics, floor maps, active stays/alerts, inventory restock, staff/guest management,
and PDF report export.
"""

import io
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from fpdf import FPDF

from .db import query_db, execute_db, get_connection


def get_admin_metrics() -> Dict[str, Any]:
    """Calculate executive KPIs: Revenue, Running Costs, Net Profit, and Room Occupancy."""
    # Financials
    rev_row = query_db("SELECT SUM(amount) as total FROM transactions WHERE type = 'Revenue'", one=True)
    revenue = float(rev_row["total"] or 0.0) if rev_row else 0.0

    util_row = query_db("SELECT SUM(amount) as total FROM transactions WHERE type = 'Cost_Utility'", one=True)
    cost_utility = float(util_row["total"] or 0.0) if util_row else 0.0

    goods_row = query_db("SELECT SUM(amount) as total FROM transactions WHERE type = 'Cost_Goods'", one=True)
    cost_goods = float(goods_row["total"] or 0.0) if goods_row else 0.0

    total_costs = cost_utility + cost_goods
    net_profit = revenue - total_costs
    profit_margin = (net_profit / revenue * 100) if revenue > 0 else 0.0

    # Guests
    guest_row = query_db("SELECT COUNT(*) as cnt FROM customers", one=True)
    total_guests = guest_row["cnt"] if guest_row else 0

    # Rooms & Occupancy
    rooms = query_db("SELECT id, room_number, status FROM rooms")
    total_rooms = len(rooms)
    vacant_count = sum(1 for r in rooms if r["status"] == "Vacant")
    occupied_count = sum(1 for r in rooms if r["status"] == "Occupied")
    service_count = sum(1 for r in rooms if r["status"] == "Needs Service")
    reserved_count = sum(1 for r in rooms if r["status"] == "Reserved")
    occupancy_pct = (occupied_count / total_rooms * 100) if total_rooms > 0 else 0.0

    # Low Stock Alerts count
    low_stock_row = query_db("SELECT COUNT(*) as cnt FROM inventory WHERE quantity <= low_stock_threshold", one=True)
    low_stock_count = low_stock_row["cnt"] if low_stock_row else 0

    # Recent Transactions for Financial Feed
    recent_transactions = query_db("""
        SELECT t.id, t.type, t.amount, t.description, t.date_recorded, c.name as customer_name
        FROM transactions t
        LEFT JOIN customers c ON t.customer_id = c.id
        ORDER BY t.date_recorded DESC LIMIT 8
    """)

    return {
        "revenue": revenue,
        "cost_utility": cost_utility,
        "cost_goods": cost_goods,
        "total_costs": total_costs,
        "net_profit": net_profit,
        "profit_margin": profit_margin,
        "total_guests": total_guests,
        "total_rooms": total_rooms,
        "vacant_count": vacant_count,
        "occupied_count": occupied_count,
        "service_count": service_count,
        "reserved_count": reserved_count,
        "occupancy_pct": occupancy_pct,
        "low_stock_count": low_stock_count,
        "recent_transactions": recent_transactions
    }


def get_active_stays_and_alerts() -> List[Dict[str, Any]]:
    """Retrieve active guest stays with real-time Overdue / Near-Overdue status flags."""
    today = date.today()
    sql = """
        SELECT r.id as res_id, r.check_in_date, r.check_out_date, r.status as res_status,
               rm.room_number, rm.type as room_type, rm.price_per_night,
               c.id as customer_id, c.name as customer_name, c.mobile_number, c.email, c.image_path as customer_image
        FROM reservations r
        JOIN rooms rm ON r.room_id = rm.id
        JOIN customers c ON r.customer_id = c.id
        WHERE r.status = 'Checked In'
        ORDER BY r.check_out_date ASC
    """
    rows = query_db(sql)
    results = []
    for row in rows:
        item = dict(row)
        co_str = item.get("check_out_date")
        alert_status = "Active"
        alert_badge = "success"
        days_diff = 0

        if co_str:
            try:
                co_date = datetime.strptime(co_str[:10], "%Y-%m-%d").date()
                days_diff = (co_date - today).days
                if days_diff < 0:
                    alert_status = f"OVERDUE ({abs(days_diff)}d)"
                    alert_badge = "danger"
                elif days_diff == 0:
                    alert_status = "DUE TODAY"
                    alert_badge = "warning"
                elif days_diff == 1:
                    alert_status = "Due Tomorrow"
                    alert_badge = "info"
                else:
                    alert_status = f"{days_diff} days left"
                    alert_badge = "success"
            except Exception:
                pass

        item["alert_status"] = alert_status
        item["alert_badge"] = alert_badge
        item["days_diff"] = days_diff
        results.append(item)

    return results


def get_floor_rooms(utilities_mode: bool = False, floor: Optional[int] = None, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve room list with current occupants and statuses.
    If utilities_mode is True, strictly hide Vacant rooms per hotel operational security policy.
    """
    sql = """
        SELECT rm.id, rm.room_number, rm.type, rm.price_per_night, rm.status, rm.is_reserved, rm.is_occupied, rm.packs,
               c.name as current_guest, c.mobile_number as guest_phone, r.check_in_date, r.check_out_date, r.id as res_id
        FROM rooms rm
        LEFT JOIN reservations r ON rm.id = r.room_id AND r.status = 'Checked In'
        LEFT JOIN customers c ON r.customer_id = c.id
    """
    conditions = []
    args = []

    if utilities_mode:
        # Strictly hide vacant/empty rooms for utilities view
        conditions.append("rm.status != 'Vacant'")

    if status_filter and status_filter != "All":
        conditions.append("rm.status = ?")
        args.append(status_filter)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY rm.room_number ASC"
    rows = query_db(sql, args)

    filtered = []
    for r in rows:
        room_dict = dict(r)
        # Determine floor from room number (e.g. 101 -> Floor 1, 202 -> Floor 2)
        try:
            r_num = int(room_dict["room_number"])
            room_floor = r_num // 100
        except Exception:
            room_floor = 1

        room_dict["floor"] = room_floor
        if floor and room_floor != floor:
            continue
        filtered.append(room_dict)

    return filtered


def get_inventory_items(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve inventory items with low-stock status calculation."""
    sql = "SELECT id, item_name, category, quantity, low_stock_threshold, unit, cost_per_unit FROM inventory"
    args = []
    if category and category != "All":
        sql += " WHERE category = ?"
        args.append(category)
    sql += " ORDER BY (quantity <= low_stock_threshold) DESC, item_name ASC"
    items = query_db(sql, args)
    for it in items:
        it["is_low"] = it["quantity"] <= it["low_stock_threshold"]
    return items


def restock_inventory_item(item_id: int, added_qty: int, unit_cost: float, admin_name: str = "Admin") -> bool:
    """Increase stock quantity and record transaction cost."""
    item = query_db("SELECT id, item_name, quantity, cost_per_unit FROM inventory WHERE id = ?", (item_id,), one=True)
    if not item:
        return False

    new_qty = item["quantity"] + added_qty
    total_cost = added_qty * unit_cost

    execute_db("UPDATE inventory SET quantity = ?, cost_per_unit = ? WHERE id = ?", (new_qty, unit_cost, item_id))
    execute_db("""
        INSERT INTO transactions (type, amount, description, date_recorded)
        VALUES ('Cost_Goods', ?, ?, CURRENT_TIMESTAMP)
    """, (total_cost, f"Restock: {added_qty} {item['item_name']} @ PHP {unit_cost:.2f} by {admin_name}"))
    return True


def get_all_employees() -> List[Dict[str, Any]]:
    """Retrieve all staff accounts for admin management."""
    return query_db("""
        SELECT id, username, role, name, phone, email, image_path, is_active
        FROM users
        ORDER BY is_active DESC, role ASC, name ASC
    """)


def toggle_employee_status(user_id: int) -> bool:
    """Toggle active/inactive status of staff account."""
    user = query_db("SELECT is_active FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        return False
    new_status = 0 if user["is_active"] else 1
    execute_db("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    return True


def get_all_customers(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve registered customer records with loyalty points balance."""
    sql = """
        SELECT c.id, c.name, c.email, c.mobile_number, c.loyalty_points, c.image_path,
               (SELECT COUNT(*) FROM reservations WHERE customer_id = c.id) as stay_count
        FROM customers c
    """
    args = []
    if search:
        sql += " WHERE c.name LIKE ? OR c.email LIKE ? OR c.mobile_number LIKE ?"
        like = f"%{search}%"
        args = [like, like, like]
    sql += " ORDER BY c.loyalty_points DESC, c.name ASC"
    return query_db(sql, args)


def adjust_customer_points(customer_id: int, points_delta: int) -> bool:
    """Adjust guest loyalty rewards points."""
    cust = query_db("SELECT loyalty_points FROM customers WHERE id = ?", (customer_id,), one=True)
    if not cust:
        return False
    new_pts = max(0, cust["loyalty_points"] + points_delta)
    execute_db("UPDATE customers SET loyalty_points = ? WHERE id = ?", (new_pts, customer_id))
    return True


def get_loyalty_rewards() -> List[Dict[str, Any]]:
    """Retrieve catalog of redeemable loyalty rewards."""
    return query_db("SELECT id, reward_name, points_required, description FROM loyalty_rewards ORDER BY points_required ASC")


def add_loyalty_reward(reward_name: str, points_required: int, description: str) -> int:
    """Add new loyalty reward attainment."""
    return execute_db("""
        INSERT INTO loyalty_rewards (reward_name, points_required, description)
        VALUES (?, ?, ?)
    """, (reward_name, points_required, description))


def delete_loyalty_reward(reward_id: int) -> bool:
    """Remove loyalty reward."""
    execute_db("DELETE FROM loyalty_rewards WHERE id = ?", (reward_id,))
    return True


class MobileAuditPDF(FPDF):
    """Generates elegant executive PDF audit reports matching the brand identity."""
    def header(self):
        # Royal Purple Header Bar
        self.set_fill_color(59, 24, 95)
        self.rect(0, 0, 210, 8, "F")
        # Gold Accent Line
        self.set_fill_color(245, 158, 11)
        self.rect(0, 8, 210, 2, "F")
        self.ln(6)
        self.set_font("Arial", "B", 18)
        self.set_text_color(59, 24, 95)
        self.cell(0, 8, "THE QUEST HOTEL", ln=True, align="C")
        self.set_font("Arial", "I", 9)
        self.set_text_color(120, 53, 15)
        self.cell(0, 5, '"We shall never deny a guest, even the most ridiculous request"', ln=True, align="C")
        self.set_font("Arial", "B", 11)
        self.set_text_color(30, 41, 59)
        self.cell(0, 7, "MOBILE AUDIT & EXECUTIVE FINANCIAL REPORT", ln=True, align="C")
        self.set_draw_color(226, 232, 240)
        self.line(10, 32, 200, 32)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"The Quest Hotel Mobile Portal | Confidential | Page {self.page_no()}", align="C")


def generate_executive_pdf_report(admin_name: str = "Administrator") -> bytes:
    """Produce binary PDF bytes for instant browser download."""
    metrics = get_admin_metrics()
    now_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    pdf = MobileAuditPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Generation metadata
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(100, 6, f"Generated On: {now_str}", ln=False)
    pdf.cell(90, 6, f"Auditor: {admin_name}", ln=True, align="R")
    pdf.ln(3)

    # Executive Summary Box
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(10, pdf.get_y(), 190, 26, "DF")

    start_y = pdf.get_y() + 2
    pdf.set_xy(12, start_y)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(45, 5, "Total Revenue:", ln=False)
    pdf.cell(50, 5, "Total Running Costs:", ln=False)
    pdf.cell(50, 5, "Net Hotel Profit:", ln=False)
    pdf.cell(40, 5, "Total Guests:", ln=True)

    pdf.set_xy(12, start_y + 6)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(45, 6, f"PHP {metrics['revenue']:,.2f}", ln=False)

    pdf.set_text_color(239, 68, 68)
    pdf.cell(50, 6, f"PHP {metrics['total_costs']:,.2f}", ln=False)

    pdf.set_text_color(59, 24, 95)
    pdf.cell(50, 6, f"PHP {metrics['net_profit']:,.2f}", ln=False)

    pdf.set_text_color(245, 158, 11)
    pdf.cell(40, 6, f"{metrics['total_guests']} guests", ln=True)

    pdf.set_xy(12, start_y + 13)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(45, 4, f"Utility: PHP {metrics['cost_utility']:,.2f}", ln=False)
    pdf.cell(50, 4, f"Goods: PHP {metrics['cost_goods']:,.2f}", ln=False)
    pdf.cell(50, 4, f"Margin: {metrics['profit_margin']:.1f}%", ln=False)
    pdf.cell(40, 4, f"Occupancy: {metrics['occupancy_pct']:.1f}%", ln=True)

    pdf.set_y(start_y + 24)
    pdf.ln(4)

    # Room Breakdown Section
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(0, 6, "1. Room Occupancy & Floor Distribution", ln=True)

    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(30, 41, 59)
    status_summary = (
        f"Occupied: {metrics['occupied_count']}   |   "
        f"Vacant: {metrics['vacant_count']}   |   "
        f"Needs Service: {metrics['service_count']}   |   "
        f"Reserved: {metrics['reserved_count']}   |   "
        f"Total Inventory: {metrics['total_rooms']} Suites"
    )
    pdf.cell(0, 6, status_summary, ln=True)
    pdf.ln(3)

    # Recent Transactions Section
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(59, 24, 95)
    pdf.cell(0, 6, "2. Recent Financial Transactions", ln=True)

    pdf.set_fill_color(59, 24, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(30, 6, "Date", border=1, fill=True)
    pdf.cell(30, 6, "Type", border=1, fill=True)
    pdf.cell(90, 6, "Description / Party", border=1, fill=True)
    pdf.cell(40, 6, "Amount (PHP)", border=1, ln=True, align="R", fill=True)

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(30, 41, 59)
    for tx in metrics["recent_transactions"]:
        date_short = str(tx["date_recorded"])[:16]
        desc = (tx["description"] or "")[:48]
        amt = float(tx["amount"] or 0)
        is_rev = tx["type"] == "Revenue"
        amt_str = f"+{amt:,.2f}" if is_rev else f"-{amt:,.2f}"

        pdf.cell(30, 5, date_short, border=1)
        pdf.cell(30, 5, tx["type"], border=1)
        pdf.cell(90, 5, desc, border=1)
        pdf.cell(40, 5, amt_str, border=1, ln=True, align="R")

    # Output to byte buffer
    return pdf.output(dest="S").encode("latin-1")
