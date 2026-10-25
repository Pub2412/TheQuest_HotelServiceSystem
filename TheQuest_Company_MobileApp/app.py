import hashlib
import hmac
import sqlite3
import time
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_from_directory, session, url_for


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "hotel_service.db"

app = Flask(__name__)
app.secret_key = "the-quest-mobile-development-key"
app.config["DATABASE"] = str(DATABASE_PATH)


def get_connection():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def verify_password(password, stored_hash):
    if not stored_hash:
        return False
    try:
        if "$" not in stored_hash:
            return hmac.compare_digest(password, stored_hash)
        salt_hex, hash_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        for iterations in (100_000, 600_000):
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, iterations
            )
            if hmac.compare_digest(actual, expected):
                return True
    except (TypeError, ValueError):
        return False
    return False


@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}


def login_required(view):
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def role_required(*roles):
    def decorator(view):
        protected = login_required(view)

        def wrapped(*args, **kwargs):
            user = session.get("user", {})
            if user.get("role") not in roles:
                return redirect(url_for("dashboard"))
            return protected(*args, **kwargs)

        wrapped.__name__ = view.__name__
        return wrapped

    return decorator


@app.after_request
def prevent_cached_pages(response):
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.get("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(PROJECT_ROOT / "assets", filename)


@app.route("/", methods=["GET", "POST"])
def login():
    lockout_until = session.get("lockout_until", 0)
    if lockout_until > time.time():
        remaining = int(lockout_until - time.time()) + 1
        return render_template(
            "login.html",
            error=f"Too many failed attempts. Try again in {remaining} seconds.",
        )
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_connection() as connection:
            user = connection.execute(
                "SELECT id, username, password_hash, role, name "
                "FROM users WHERE username = ? AND is_active = 1",
                (username,),
            ).fetchone()
        if user and verify_password(password, user["password_hash"]):
            session.pop("failed_attempts", None)
            session.pop("lockout_until", None)
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "name": user["name"],
            }
            return redirect(url_for("dashboard"))
        failed_attempts = session.get("failed_attempts", 0) + 1
        session["failed_attempts"] = failed_attempts
        if failed_attempts >= 3:
            session["failed_attempts"] = 0
            session["lockout_until"] = time.time() + 60
        return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    response = redirect(url_for("login"))
    response.delete_cookie("session")
    return response


@app.get("/dashboard")
@login_required
def dashboard():
    with get_connection() as connection:
        metrics = {
            "rooms": connection.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
            "occupied": connection.execute(
                "SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'"
            ).fetchone()[0],
            "vacant": connection.execute(
                "SELECT COUNT(*) FROM rooms WHERE status = 'Vacant'"
            ).fetchone()[0],
            "pending": connection.execute(
                "SELECT COUNT(*) FROM reservations WHERE status = 'Pending'"
            ).fetchone()[0],
        }
        rooms = connection.execute(
            "SELECT room_number, type, price_per_night, status "
            "FROM rooms ORDER BY room_number"
        ).fetchall()
    return render_template("dashboard.html", metrics=metrics, rooms=rooms)


def render_data_page(title, description, columns, rows, actions=None, form=None):
    return render_template(
        "page.html",
        title=title,
        description=description,
        columns=columns,
        rows=rows,
        actions=actions or [],
        form=form,
    )


@app.get("/admin/analytics")
@role_required("Admin")
def admin_analytics():
    with get_connection() as connection:
        metrics = connection.execute(
            "SELECT type, COALESCE(SUM(amount), 0) AS total FROM transactions GROUP BY type"
        ).fetchall()
        rows = connection.execute(
            "SELECT date_recorded, type, amount, description "
            "FROM transactions ORDER BY date_recorded DESC LIMIT 100"
        ).fetchall()
    totals = {row["type"]: row["total"] for row in metrics}
    return render_data_page(
        "Executive Analytics",
        f"Revenue: ₱{totals.get('Revenue', 0):,.2f} | "
        f"Running costs: ₱{totals.get('Cost_Utility', 0) + totals.get('Cost_Goods', 0):,.2f}",
        ["Date", "Type", "Amount", "Description"], rows,
        [("Dashboard", "dashboard"), ("Inventory", "admin_inventory"),
         ("Rewards", "admin_rewards"), ("Bulletin", "bulletin")],
    )


@app.route("/admin/rewards", methods=["GET", "POST"])
@role_required("Admin")
def admin_rewards():
    if request.method == "POST":
        action = request.form.get("action")
        with get_connection() as connection:
            if action == "create":
                connection.execute(
                    "INSERT INTO loyalty_rewards (reward_name, points_required, description) "
                    "VALUES (?, ?, ?)",
                    (request.form.get("reward_name", "").strip(),
                     request.form.get("points_required", type=int),
                     request.form.get("description", "").strip()),
                )
            elif action == "delete":
                connection.execute(
                    "DELETE FROM loyalty_rewards WHERE id = ?",
                    (request.form.get("reward_id", type=int),),
                )
            connection.commit()
        return redirect(url_for("admin_rewards"))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, reward_name, points_required, description "
            "FROM loyalty_rewards ORDER BY points_required"
        ).fetchall()
    return render_data_page(
        "Loyalty Rewards", "Manage promotional rewards and point requirements.",
        ["ID", "Reward", "Points", "Description"], rows,
        [("Dashboard", "dashboard"), ("Analytics", "admin_analytics"),
         ("Guests", "admin_guests")],
        {"action": "create", "submit": "Add reward", "fields": [
            ("reward_name", "Reward name", "text"),
            ("points_required", "Points required", "number"),
            ("description", "Description", "textarea"),
        ]},
    )


@app.route("/admin/inventory", methods=["GET", "POST"])
@role_required("Admin")
def admin_inventory():
    if request.method == "POST":
        item_id = request.form.get("item_id", type=int)
        quantity = request.form.get("quantity", type=int)
        if item_id and quantity and quantity > 0:
            with get_connection() as connection:
                item = connection.execute(
                    "SELECT item_name, cost_per_unit FROM inventory WHERE id = ?",
                    (item_id,),
                ).fetchone()
                if item:
                    connection.execute(
                        "UPDATE inventory SET quantity = quantity + ? WHERE id = ?",
                        (quantity, item_id),
                    )
                    connection.execute(
                        "INSERT INTO transactions (type, amount, description) "
                        "VALUES ('Cost_Goods', ?, ?)",
                        (quantity * (item["cost_per_unit"] or 0),
                         f"Restocked {quantity} {item['item_name']}"),
                    )
                    connection.commit()
        return redirect(url_for("admin_inventory"))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, item_name, category, quantity, unit, low_stock_threshold "
            "FROM inventory ORDER BY item_name"
        ).fetchall()
    return render_data_page(
        "Inventory", "Manage kitchen and utility stock.",
        ["ID", "Item", "Category", "Quantity", "Unit", "Threshold"],
        rows, [("Dashboard", "dashboard"), ("Staff", "admin_staff"), ("Guests", "admin_guests")],
        {"fields": [("item_id", "Inventory ID", "number"), ("quantity", "Quantity to add", "number")],
         "submit": "Restock inventory"},
    )


@app.route("/admin/staff", methods=["GET", "POST"])
@role_required("Admin")
def admin_staff():
    if request.method == "POST":
        action = request.form.get("action")
        with get_connection() as connection:
            if action == "create":
                username = request.form.get("username", "").strip()
                name = request.form.get("name", "").strip()
                role = request.form.get("role", "")
                password = request.form.get("password", "")
                if username and name and role and password:
                    salt = hashlib.sha256(password.encode("utf-8")).digest()[:16]
                    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
                    connection.execute(
                        "INSERT OR IGNORE INTO users "
                        "(username, password_hash, role, name, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                        (username, f"{salt.hex()}${digest.hex()}", role, name,
                         request.form.get("phone"), request.form.get("email")),
                    )
            elif action == "toggle":
                connection.execute(
                    "UPDATE users SET is_active = CASE is_active WHEN 1 THEN 0 ELSE 1 END "
                    "WHERE id = ?", (request.form.get("user_id", type=int),)
                )
            connection.commit()
        return redirect(url_for("admin_staff"))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT name, username, role, phone, email FROM users ORDER BY name"
        ).fetchall()
    return render_data_page(
        "Staff", "Employee accounts and roles.",
        ["Name", "Username", "Role", "Phone", "Email"],
        rows, [("Dashboard", "dashboard"), ("Inventory", "admin_inventory"), ("Guests", "admin_guests")],
        {"action": "create", "submit": "Create staff account", "fields": [
            ("name", "Name", "text"), ("username", "Username", "text"),
            ("password", "Temporary password", "password"),
            ("role", "Role (Admin/Cashier/Staff_Kitchen/Staff_Logistics/Staff_Utilities)", "text"),
            ("phone", "Phone", "tel"), ("email", "Email", "email"),
        ]},
    )


@app.route("/admin/guests", methods=["GET", "POST"])
@role_required("Admin")
def admin_guests():
    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        points = request.form.get("points", type=int)
        if customer_id is not None and points is not None:
            with get_connection() as connection:
                connection.execute(
                    "UPDATE customers SET loyalty_points = ? WHERE id = ?",
                    (max(0, points), customer_id),
                )
                connection.commit()
        return redirect(url_for("admin_guests"))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, email, mobile_number, loyalty_points FROM customers ORDER BY name"
        ).fetchall()
    return render_data_page(
        "Guests", "Registered hotel customers.",
        ["ID", "Name", "Email", "Mobile", "Points"],
        rows, [("Dashboard", "dashboard"), ("Inventory", "admin_inventory"), ("Staff", "admin_staff")],
        {"fields": [("customer_id", "Customer ID", "number"), ("points", "New loyalty points", "number")],
         "submit": "Update loyalty points"},
    )


@app.get("/cashier/reservations")
@role_required("Cashier")
def cashier_reservations():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT res.id, c.name, r.room_number, res.check_in_date, "
            "res.check_out_date, res.status FROM reservations res "
            "JOIN customers c ON c.id = res.customer_id "
            "JOIN rooms r ON r.id = res.room_id ORDER BY res.id DESC"
        ).fetchall()
    return render_data_page(
        "Reservations", "Manage guest bookings and check-in status.",
        ["Reservation", "Guest", "Room", "Check-in", "Check-out", "Status"],
        rows, [("Dashboard", "dashboard"), ("Guests", "cashier_guests")],
        {"submit": "Update reservation status", "action_template": "/cashier/reservations/status",
         "fields": [
            ("reservation_id", "Reservation ID", "number"),
            ("status", "New status (Pending/Checked In/Checked Out/Canceled)", "text"),
        ]},
    )


@app.post("/cashier/reservations/<int:reservation_id>/status")
@role_required("Cashier")
def update_reservation_status(reservation_id):
    new_status = request.form.get("status")
    if new_status not in {"Pending", "Checked In", "Checked Out", "Canceled"}:
        return redirect(url_for("cashier_reservations"))
    with get_connection() as connection:
        connection.execute(
            "UPDATE reservations SET status = ? WHERE id = ?",
            (new_status, reservation_id),
        )
        connection.commit()
    return redirect(url_for("cashier_reservations"))


@app.post("/cashier/reservations/status")
@role_required("Cashier")
def update_reservation_status_from_form():
    reservation_id = request.form.get("reservation_id", type=int)
    return update_reservation_status(reservation_id or 0)


@app.get("/cashier/guests")
@role_required("Cashier")
def cashier_guests():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT c.name, c.email, c.mobile_number, "
            "COALESCE(r.room_number, 'Not Checked In') AS room "
            "FROM customers c LEFT JOIN reservations res "
            "ON res.customer_id = c.id AND res.status = 'Checked In' "
            "LEFT JOIN rooms r ON r.id = res.room_id ORDER BY c.name"
        ).fetchall()
    return render_data_page(
        "Guests", "Guest directory and active stays.",
        ["Name", "Email", "Mobile", "Room"],
        rows, [("Dashboard", "dashboard"), ("Reservations", "cashier_reservations")],
    )


@app.route("/bulletin", methods=["GET", "POST"])
@login_required
def bulletin():
    if request.method == "POST" and session["user"]["role"] == "Admin":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if title and content:
            with get_connection() as connection:
                connection.execute(
                    "INSERT INTO bulletin (author_id, title, content) VALUES (?, ?, ?)",
                    (session["user"]["id"], title, content),
                )
                connection.commit()
        return redirect(url_for("bulletin"))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT b.title, b.content, u.name, b.timestamp "
            "FROM bulletin b LEFT JOIN users u ON u.id = b.author_id "
            "ORDER BY b.timestamp DESC"
        ).fetchall()
    form = None
    if session["user"]["role"] == "Admin":
        form = {"submit": "Post announcement", "fields": [
            ("title", "Announcement title", "text"),
            ("content", "Announcement", "textarea"),
        ]}
    return render_data_page(
        "Employee Bulletin", "Official announcements for hotel employees.",
        ["Title", "Message", "Author", "Posted"], rows,
        [("Dashboard", "dashboard"), ("Inbox", "inbox")], form,
    )


@app.route("/inbox", methods=["GET", "POST"])
@login_required
def inbox():
    user_id = session["user"]["id"]
    if request.method == "POST":
        receiver_role = request.form.get("receiver_role", "").strip()
        content = request.form.get("content", "").strip()
        if receiver_role and content:
            with get_connection() as connection:
                receiver = connection.execute(
                    "SELECT id FROM users WHERE role = ? AND is_active = 1 "
                    "ORDER BY id LIMIT 1", (receiver_role,),
                ).fetchone()
                connection.execute(
                    "INSERT INTO messages (sender_id, receiver_id, receiver_role, content) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, receiver["id"] if receiver else None, receiver_role, content),
                )
                connection.commit()
        return redirect(url_for("inbox"))
    with get_connection() as connection:
        recipient_roles = [
            row["role"] for row in connection.execute(
                "SELECT DISTINCT role FROM users WHERE is_active = 1 "
                "AND role <> ? ORDER BY role", (session["user"]["role"],)
            ).fetchall()
        ]
        rows = connection.execute(
            "SELECT m.content, COALESCE(s.name, m.receiver_role) AS recipient, "
            "m.timestamp FROM messages m LEFT JOIN users s ON s.id = m.sender_id "
            "WHERE m.sender_id = ? OR m.receiver_id = ? OR m.receiver_role = ? "
            "ORDER BY m.timestamp DESC",
            (user_id, user_id, session["user"]["role"]),
        ).fetchall()
    return render_data_page(
        "Employee Inbox", "Send and review staff messages.",
        ["Message", "Recipient", "Time"], rows,
        [("Dashboard", "dashboard"), ("Bulletin", "bulletin")],
        {"submit": "Send message", "fields": [
            ("receiver_role", "Recipient role", "select", recipient_roles),
            ("content", "Message", "textarea"),
        ]},
    )


@app.get("/map")
@login_required
def room_map():
    status = request.args.get("status", "All")
    with get_connection() as connection:
        if status == "All":
            rooms = connection.execute(
                "SELECT room_number, type, status, price_per_night FROM rooms "
                "ORDER BY room_number"
            ).fetchall()
        else:
            rooms = connection.execute(
                "SELECT room_number, type, status, price_per_night FROM rooms "
                "WHERE status = ? ORDER BY room_number", (status,),
            ).fetchall()
    return render_data_page(
        "Hotel Room Map", "Room occupancy and service status.",
        ["Room", "Type", "Status", "Rate"], rooms,
        [("Dashboard", "dashboard"), ("All rooms", "room_map")],
    )


@app.route("/staff/<section>", methods=["GET", "POST"])
@role_required("Staff_Kitchen", "Staff_Logistics", "Staff_Utilities")
def staff_section(section):
    role = session["user"]["role"]
    if request.method == "POST":
        record_id = request.form.get("record_id", type=int)
        new_status = request.form.get("status", "")
        with get_connection() as connection:
            if role == "Staff_Logistics" and section == "logistics":
                if request.form.get("logistics_code") != "QUEST-LOG-2026":
                    return redirect(url_for("staff_section", section=section))
                if new_status in {"Completed", "Canceled", "On the Way", "Near Receive"}:
                    connection.execute(
                        "UPDATE deliveries SET status = ?, date_updated = CURRENT_TIMESTAMP WHERE id = ?",
                        (new_status, record_id),
                    )
            elif role == "Staff_Utilities" and section == "utilities":
                if new_status in {"Processing", "Complete", "Canceled"}:
                    connection.execute(
                        "UPDATE service_requests SET status = ? WHERE id = ?",
                        (new_status, record_id),
                    )
            elif role == "Staff_Kitchen" and section == "kitchen":
                if new_status in {"Processing", "Complete", "Canceled"}:
                    connection.execute(
                        "UPDATE service_requests SET status = ? WHERE id = ?",
                        (new_status, record_id),
                    )
            connection.commit()
        return redirect(url_for("staff_section", section=section))
    role_sections = {
        "Staff_Kitchen": {"kitchen": ("Kitchen Orders", "Food delivery and kitchen requests.",
                                      "SELECT id, request_type, details, status, date_created FROM service_requests ORDER BY id DESC",
                                      ["ID", "Type", "Details", "Status", "Created"])},
        "Staff_Logistics": {"logistics": ("Logistics", "Inbound deliveries and shipment tracking.",
                                          "SELECT id, description, status, logistics_code, date_updated FROM deliveries ORDER BY id DESC",
                                          ["ID", "Description", "Status", "Code", "Updated"])},
        "Staff_Utilities": {"utilities": ("Utilities", "Room service requests and room conditions.",
                                          "SELECT sr.id, r.room_number, sr.request_type, sr.status, sr.date_created "
                                          "FROM service_requests sr JOIN rooms r ON r.id = sr.room_id "
                                          "WHERE r.status <> 'Vacant' ORDER BY sr.id DESC",
                                          ["ID", "Room", "Request", "Status", "Created"])},
    }
    config = role_sections.get(session["user"]["role"], {}).get(section)
    if not config:
        return redirect(url_for("dashboard"))
    title, description, query, columns = config
    with get_connection() as connection:
        rows = connection.execute(query).fetchall()
    form = {"submit": "Update task", "fields": [
        ("record_id", "Record ID", "number"),
        ("status", "New status", "text"),
    ]}
    if role == "Staff_Logistics":
        form["fields"].append(("logistics_code", "Logistics code", "password"))
    return render_data_page(
        title, description, columns, rows,
        [("Dashboard", "dashboard"), ("Bulletin", "bulletin"), ("Inbox", "inbox")],
        form,
    )


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
