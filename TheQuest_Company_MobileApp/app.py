"""
The Quest Hotel - Mobile Application Portal.
A full mobile-first port of The Quest Hotel Management System Desktop Application.
Color Scheme: Royal Velvet Purple (#3B185F), Deep Purple (#23073D), Warm Gold (#F59E0B), Crisp White (#FFFFFF).
Slogan: "We shall never deny a guest, even the most ridiculous request"
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, send_from_directory, Response
)

# Set up module resolution
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))

from backend.db import init_database_if_needed, query_db, execute_db
from backend.auth import (
    authenticate_user, register_staff_account, get_lockout_status
)
from backend.logger import (
    log_auth_event, log_system_health, read_decrypted_auth_logs, read_system_health_logs
)
from backend.admin_service import (
    get_admin_metrics, get_active_stays_and_alerts, get_floor_rooms,
    get_inventory_items, restock_inventory_item, get_all_employees,
    toggle_employee_status, get_all_customers, adjust_customer_points,
    get_loyalty_rewards, add_loyalty_reward, delete_loyalty_reward,
    generate_executive_pdf_report
)
from backend.cashier_service import (
    get_all_reservations, get_available_rooms, create_new_reservation,
    check_in_guest, check_out_guest, change_guest_room, cancel_guest_reservation,
    create_quick_walkin_guest
)
from backend.staff_service import (
    get_kitchen_orders, update_kitchen_order_status, get_kitchen_inventory,
    get_logistics_deliveries, update_delivery_status, add_logistics_delivery,
    get_rooms_needing_service, get_utility_service_requests,
    mark_room_cleaned_and_ready, update_utility_task_status
)
from backend.communication import (
    get_bulletin_announcements, post_bulletin_announcement,
    get_user_inbox_messages, send_staff_message, get_softphone_directory
)

# Assets directory in root workspace
ASSETS_DIR = PROJECT_ROOT / "assets"

app = Flask(
    __name__,
    template_folder=str(APP_DIR / "frontend" / "templates"),
    static_folder=str(APP_DIR / "frontend" / "static")
)
app.secret_key = "thequest_mobile_secured_token_2026_royal_luxury"

# Initialize database schema/data if needed
init_database_if_needed()
log_system_health()


# ==============================================================================
# ASSETS & STATIC FILE SERVING
# ==============================================================================
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    """Serve shared images, employee portraits, room photos, and HotelMap.jpg."""
    return send_from_directory(str(ASSETS_DIR), filename)


@app.route("/manifest.json")
def serve_manifest():
    """Serve PWA manifest for mobile add-to-home-screen."""
    return send_from_directory(str(app.static_folder), "manifest.json", mimetype="application/manifest+json")


# ==============================================================================
# GLOBAL TEMPLATE CONTEXT
# ==============================================================================
@app.context_processor
def inject_globals():
    user = None
    user_id = session.get("user_id")
    if user_id:
        user = query_db("SELECT id, username, role, name, phone, email, image_path FROM users WHERE id = ?", (user_id,), one=True)
        if not user:
            session.clear()

    return {
        "current_user": user,
        "system_name": "The Quest",
        "system_subtitle": "Hotel Management System",
        "system_slogan": "We shall never deny a guest, even the most ridiculous request",
        "now_year": datetime.now().year,
        "now_time": datetime.now().strftime("%I:%M %p"),
        "now_date": datetime.now().strftime("%b %d, %Y")
    }


# ==============================================================================
# ACCESS CONTROL DECORATORS
# ==============================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in with your staff credentials.", "warning")
            return redirect(url_for("login_view"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("login_view"))
            user_role = session.get("user_role", "")
            if user_role not in allowed_roles:
                return redirect(url_for("forbidden_view", attempted=request.path))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_redirect(role: str):
    """Determine landing destination for a role."""
    if role == "Admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "Cashier":
        return redirect(url_for("cashier_reservations"))
    elif role == "Staff_Kitchen":
        return redirect(url_for("staff_kitchen"))
    elif role == "Staff_Logistics":
        return redirect(url_for("staff_logistics"))
    elif role == "Staff_Utilities":
        return redirect(url_for("staff_utilities"))
    return redirect(url_for("login_view"))


# ==============================================================================
# AUTHENTICATION & SECURITY ROUTES
# ==============================================================================
@app.route("/")
def index():
    if session.get("user_id") and session.get("user_role"):
        return role_redirect(session["user_role"])
    return redirect(url_for("login_view"))


@app.route("/login", methods=["GET", "POST"])
def login_view():
    if session.get("user_id") and session.get("user_role"):
        return role_redirect(session["user_role"])

    client_ip = request.remote_addr or "127.0.0.1"

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user, err_msg, lockout_secs = authenticate_user(username, password, client_ip)
        if user:
            session["user_id"] = user["id"]
            session["user_role"] = user["role"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name']}!", "success")
            return role_redirect(user["role"])
        else:
            flash(err_msg, "danger")
            return render_template("login.html", error=err_msg, lockout_secs=lockout_secs, username=username)

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register_view():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        ok, msg = register_staff_account(username, password, role, name, phone, email)
        if ok:
            flash("Staff account created successfully! You may now sign in.", "success")
            return redirect(url_for("login_view"))
        else:
            flash(msg, "danger")

    return render_template("register.html")


@app.route("/logout")
def logout_view():
    user_name = session.get("user_name", "Staff")
    user_role = session.get("user_role", "Unknown")
    log_auth_event("LOGOUT", user_name, user_role, "SUCCESS", "User signed out from mobile portal")
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login_view"))


@app.route("/forbidden")
def forbidden_view():
    attempted = request.args.get("attempted", "Protected Console")
    return render_template("forbidden.html", attempted_page=attempted), 403


# ==============================================================================
# ADMIN CONSOLE (Role: Admin)
# ==============================================================================
@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
@role_required("Admin")
def admin_dashboard():
    metrics = get_admin_metrics()
    active_stays = get_active_stays_and_alerts()
    return render_template("admin/dashboard.html", metrics=metrics, active_stays=active_stays)


@app.route("/admin/export-pdf")
@login_required
@role_required("Admin")
def admin_export_pdf():
    admin_name = session.get("user_name", "System Administrator")
    pdf_bytes = generate_executive_pdf_report(admin_name)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"TheQuest_Executive_Audit_{now_str}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/admin/map")
@login_required
@role_required("Admin")
def admin_map():
    floor = request.args.get("floor", type=int)
    status_filter = request.args.get("status", "All")
    rooms = get_floor_rooms(utilities_mode=False, floor=floor, status_filter=status_filter)
    return render_template("admin/map.html", rooms=rooms, current_floor=floor, current_status=status_filter)


@app.route("/admin/inventory", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def admin_inventory():
    if request.method == "POST":
        item_id = request.form.get("item_id", type=int)
        added_qty = request.form.get("added_qty", type=int, default=0)
        unit_cost = request.form.get("unit_cost", type=float, default=0.0)
        if item_id and added_qty > 0:
            admin_name = session.get("user_name", "Admin")
            if restock_inventory_item(item_id, added_qty, unit_cost, admin_name):
                flash(f"Successfully restocked {added_qty} units.", "success")
            else:
                flash("Could not complete restock.", "danger")
        return redirect(url_for("admin_inventory"))

    cat = request.args.get("category", "All")
    items = get_inventory_items(cat)
    return render_template("admin/inventory.html", items=items, current_category=cat)


@app.route("/admin/staff", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def admin_staff():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "toggle":
            uid = request.form.get("user_id", type=int)
            toggle_employee_status(uid)
            flash("Staff account status updated.", "info")
        elif action == "add":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "")
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            ok, msg = register_staff_account(username, password, role, name, phone, email)
            flash(msg, "success" if ok else "danger")
        return redirect(url_for("admin_staff"))

    employees = get_all_employees()
    return render_template("admin/staff.html", employees=employees)


@app.route("/admin/guests", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def admin_guests():
    if request.method == "POST":
        cust_id = request.form.get("customer_id", type=int)
        points_delta = request.form.get("points_delta", type=int, default=0)
        if cust_id:
            adjust_customer_points(cust_id, points_delta)
            flash(f"Loyalty balance updated by {points_delta:+d} points.", "success")
        return redirect(url_for("admin_guests"))

    q = request.args.get("q")
    customers = get_all_customers(q)
    return render_template("admin/guests.html", customers=customers, search_query=q or "")


@app.route("/admin/rewards", methods=["GET", "POST"])
@login_required
@role_required("Admin")
def admin_rewards():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("reward_name", "").strip()
            pts = request.form.get("points_required", type=int, default=100)
            desc = request.form.get("description", "").strip()
            add_loyalty_reward(name, pts, desc)
            flash("New loyalty reward created.", "success")
        elif action == "delete":
            rid = request.form.get("reward_id", type=int)
            delete_loyalty_reward(rid)
            flash("Reward removed from catalog.", "info")
        return redirect(url_for("admin_rewards"))

    rewards = get_loyalty_rewards()
    return render_template("admin/rewards.html", rewards=rewards)


@app.route("/admin/logs")
@login_required
@role_required("Admin")
def admin_logs():
    auth_logs = read_decrypted_auth_logs(limit=40)
    health_logs = read_system_health_logs(limit=25)
    return render_template("admin/logs.html", auth_logs=auth_logs, health_logs=health_logs)


# ==============================================================================
# CASHIER FRONT DESK (Role: Cashier, Admin)
# ==============================================================================
@app.route("/cashier")
@app.route("/cashier/reservations", methods=["GET", "POST"])
@login_required
@role_required("Cashier", "Admin")
def cashier_reservations():
    cashier_name = session.get("user_name", "Front Desk")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "check_in":
            res_id = request.form.get("reservation_id", type=int)
            ok, msg = check_in_guest(res_id, cashier_name)
            flash(msg, "success" if ok else "danger")

        elif action == "check_out":
            res_id = request.form.get("reservation_id", type=int)
            ok, msg, summary = check_out_guest(res_id, cashier_name)
            flash(msg, "success" if ok else "danger")

        elif action == "cancel":
            res_id = request.form.get("reservation_id", type=int)
            ok, msg = cancel_guest_reservation(res_id, cashier_name)
            flash(msg, "info" if ok else "danger")

        elif action == "change_room":
            res_id = request.form.get("reservation_id", type=int)
            new_room_id = request.form.get("new_room_id", type=int)
            ok, msg = change_guest_room(res_id, new_room_id, cashier_name)
            flash(msg, "success" if ok else "danger")

        elif action == "new_walkin":
            guest_name = request.form.get("guest_name", "").strip()
            guest_email = request.form.get("guest_email", "").strip()
            guest_phone = request.form.get("guest_phone", "").strip()
            room_id = request.form.get("room_id", type=int)
            ci = request.form.get("check_in_date")
            co = request.form.get("check_out_date")
            immediate = request.form.get("immediate_checkin") == "1"

            ok_guest, g_msg, cust_id = create_quick_walkin_guest(guest_name, guest_email, guest_phone)
            if ok_guest and cust_id:
                ok_res, res_msg, _ = create_new_reservation(cust_id, room_id, ci, co, immediate, cashier_name)
                flash(res_msg, "success" if ok_res else "danger")
            else:
                flash(g_msg, "danger")

        return redirect(url_for("cashier_reservations"))

    status = request.args.get("status", "All")
    search = request.args.get("q")
    reservations = get_all_reservations(status, search)
    vacant_rooms = get_available_rooms()
    return render_template("cashier/reservations.html", reservations=reservations, vacant_rooms=vacant_rooms, current_status=status, search_query=search or "")


@app.route("/cashier/map")
@login_required
@role_required("Cashier", "Admin")
def cashier_map():
    floor = request.args.get("floor", type=int)
    status_filter = request.args.get("status", "All")
    rooms = get_floor_rooms(utilities_mode=False, floor=floor, status_filter=status_filter)
    return render_template("cashier/map.html", rooms=rooms, current_floor=floor, current_status=status_filter)


@app.route("/cashier/guests")
@login_required
@role_required("Cashier", "Admin")
def cashier_guests():
    q = request.args.get("q")
    customers = get_all_customers(q)
    return render_template("cashier/guests.html", customers=customers, search_query=q or "")


# ==============================================================================
# STAFF OPERATIONS (Kitchen, Logistics, Utilities)
# ==============================================================================
@app.route("/staff/kitchen", methods=["GET", "POST"])
@login_required
@role_required("Staff_Kitchen", "Admin")
def staff_kitchen():
    staff_name = session.get("user_name", "Kitchen Staff")
    if request.method == "POST":
        req_id = request.form.get("request_id", type=int)
        new_status = request.form.get("new_status")
        ok, msg = update_kitchen_order_status(req_id, new_status, staff_name)
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("staff_kitchen"))

    orders = get_kitchen_orders()
    inventory = get_kitchen_inventory()
    return render_template("staff/kitchen.html", orders=orders, inventory=inventory)


@app.route("/staff/logistics", methods=["GET", "POST"])
@login_required
@role_required("Staff_Logistics", "Admin")
def staff_logistics():
    staff_name = session.get("user_name", "Logistics Officer")
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_status":
            del_id = request.form.get("delivery_id", type=int)
            new_status = request.form.get("new_status")
            passcode = request.form.get("passcode", "")
            ok, msg = update_delivery_status(del_id, new_status, passcode, staff_name)
            flash(msg, "success" if ok else "danger")
        elif action == "new_delivery":
            desc = request.form.get("description", "").strip()
            code = request.form.get("logistics_code", "").strip()
            init_stat = request.form.get("status", "Will be Shipped")
            add_logistics_delivery(desc, code, init_stat)
            flash("Shipment recorded.", "success")
        return redirect(url_for("staff_logistics"))

    status = request.args.get("status", "All")
    deliveries = get_logistics_deliveries(status)
    return render_template("staff/logistics.html", deliveries=deliveries, current_status=status)


@app.route("/staff/utilities", methods=["GET", "POST"])
@login_required
@role_required("Staff_Utilities", "Admin")
def staff_utilities():
    staff_name = session.get("user_name", "Housekeeping Attendant")
    if request.method == "POST":
        action = request.form.get("action")
        if action == "clean_room":
            room_id = request.form.get("room_id", type=int)
            ok, msg = mark_room_cleaned_and_ready(room_id, staff_name)
            flash(msg, "success" if ok else "danger")
        elif action == "update_task":
            task_id = request.form.get("task_id", type=int)
            new_stat = request.form.get("new_status")
            ok, msg = update_utility_task_status(task_id, new_stat, staff_name)
            flash(msg, "success" if ok else "danger")
        return redirect(url_for("staff_utilities"))

    dirty_rooms = get_rooms_needing_service()
    service_tasks = get_utility_service_requests()
    # Floor map with strictly hidden vacant rooms
    rooms = get_floor_rooms(utilities_mode=True)
    return render_template("staff/utilities.html", dirty_rooms=dirty_rooms, service_tasks=service_tasks, rooms=rooms)


# ==============================================================================
# SHARED STAFF MODULES: BULLETIN & INBOX & SOFTPHONE
# ==============================================================================
@app.route("/bulletin", methods=["GET", "POST"])
@login_required
def bulletin_view():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        author_id = session.get("user_id")
        if title and content and author_id:
            post_bulletin_announcement(author_id, title, content)
            flash("Announcement posted to company bulletin.", "success")
            return redirect(url_for("bulletin_view"))
        flash("Title and message content cannot be empty.", "warning")

    posts = get_bulletin_announcements()
    return render_template("shared/bulletin.html", posts=posts)


@app.route("/inbox", methods=["GET", "POST"])
@login_required
def inbox_view():
    user_id = session.get("user_id")
    user_role = session.get("user_role", "")

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        receiver_id = request.form.get("receiver_id", type=int)
        receiver_role = request.form.get("receiver_role")

        if content:
            send_staff_message(user_id, content, receiver_id, receiver_role)
            flash("Message dispatched.", "success")
            return redirect(url_for("inbox_view"))
        flash("Message content is required.", "warning")

    messages = get_user_inbox_messages(user_id, user_role)
    contacts = get_softphone_directory(exclude_user_id=user_id)
    return render_template("shared/inbox.html", messages=messages, contacts=contacts)


@app.route("/api/softphone/contacts")
@login_required
def api_softphone_contacts():
    user_id = session.get("user_id")
    contacts = get_softphone_directory(exclude_user_id=user_id)
    return jsonify(contacts)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"[The Quest Mobile App] Server online on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
