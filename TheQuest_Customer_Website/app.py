"""
The Quest Hotel - Customer Website Main Application.
Theme: Royal Purple, Warm Amber Gold, and Crisp White.
Tagline: "We shall never deny a guest, even the most ridiculous request"
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify, session,
    redirect, url_for, send_from_directory, flash
)

# Add current folder to sys.path so backend package is importable
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))

from backend.db import (
    init_customer_tables, get_customer_by_id, get_active_stay, get_connection
)
from backend.auth import (
    authenticate_customer, register_customer, reset_password,
    social_login, hash_password, check_lockout, validate_profile_image,
    store_profile_image
)
from backend.hotel_data import (
    PROMOTIONS_DATA, ROOM_METADATA, get_all_rooms, get_room_by_id,
    create_reservation, extend_reservation, get_food_menu, get_hotel_services,
    create_food_order, create_service_booking, create_ridiculous_request,
    get_loyalty_rewards, redeem_loyalty_reward, get_customer_vouchers,
    get_customer_reservations, send_inquiry, request_callback, get_inquiries_history
)

# Assets directory in root workspace
ASSETS_DIR = PROJECT_ROOT / "assets"

app = Flask(
    __name__,
    template_folder=str(APP_DIR / "frontend" / "templates"),
    static_folder=str(APP_DIR / "frontend" / "static")
)
app.secret_key = "thequest_luxury_secret_key_2026_guests_first"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# Initialize auxiliary customer tables on startup
init_customer_tables()

# ==============================================================================
# STATIC ASSETS ROUTE (Serve assets directly from ../assets without duplication)
# ==============================================================================
@app.route("/assets/<path:filename>")
def serve_shared_assets(filename):
    """Serve shared images, logos, food photos, and room photos from assets/ directory."""
    return send_from_directory(str(ASSETS_DIR), filename)

# ==============================================================================
# TEMPLATE CONTEXT PROCESSOR (Global variables available in all Jinja templates)
# ==============================================================================
@app.context_processor
def inject_global_context():
    customer = None
    active_stay = None
    customer_id = session.get("customer_id")
    if customer_id:
        customer = get_customer_by_id(customer_id)
        if customer:
            active_stay = get_active_stay(customer_id)
        else:
            session.pop("customer_id", None)

    return {
        "current_user": customer,
        "active_stay": active_stay,
        "is_checked_in": active_stay is not None,
        "system_name": "The Quest Hotel",
        "system_slogan": "We shall never deny a guest, even the most ridiculous request",
        "now_year": datetime.now().year
    }

# ==============================================================================
# PAGE ROUTES
# ==============================================================================
@app.route("/")
def index():
    """Home view featuring promotional carousel, quick access cards, and live stay widget."""
    customer_id = session.get("customer_id")
    active_stay = get_active_stay(customer_id) if customer_id else None
    featured_rooms = get_all_rooms()[:4]
    return render_template(
        "index.html",
        promotions=PROMOTIONS_DATA,
        active_stay=active_stay,
        featured_rooms=featured_rooms
    )

@app.route("/rooms")
def rooms_view():
    """Make Reservation / Extend Reservation view. Reservations are for logged in customers only."""
    category_filter = request.args.get("category")
    all_rooms = get_all_rooms(category_filter)
    categories = ["All", "Standard Ground", "Deluxe", "Deluxe Balcony", "Executive Suite", "Penthouse & VIP"]
    return render_template(
        "rooms.html",
        rooms=all_rooms,
        categories=categories,
        selected_category=category_filter or "All"
    )

@app.route("/services")
def services_view():
    """Request Service view: Food delivery menu, hotel services, and the ridiculous request concierge."""
    food_menu = get_food_menu()
    hotel_services = get_hotel_services()
    return render_template(
        "services.html",
        food_menu=food_menu,
        hotel_services=hotel_services
    )

@app.route("/ask")
def ask_view():
    """Ask Questions view: Live Front Desk & Concierge messaging and instant desk callback."""
    customer_id = session.get("customer_id")
    inquiries = get_inquiries_history(customer_id) if customer_id else []
    return render_template(
        "ask.html",
        inquiries=inquiries
    )

@app.route("/rewards")
def rewards_view():
    """Loyalty Rewards view: Earned points balance, VIP tier status, and redeemable rewards catalog."""
    customer_id = session.get("customer_id")
    rewards = get_loyalty_rewards()
    vouchers = get_customer_vouchers(customer_id) if customer_id else []
    return render_template(
        "rewards.html",
        rewards=rewards,
        vouchers=vouchers
    )

@app.route("/profile")
def profile_view():
    """Profile RUD view: Personal details, linked social accounts, and reservation history."""
    customer_id = session.get("customer_id")
    if not customer_id:
        flash("Please log in to view your profile.", "info")
        return redirect(url_for("index") + "?open_login=true")

    customer = get_customer_by_id(customer_id)
    reservations = get_customer_reservations(customer_id)
    vouchers = get_customer_vouchers(customer_id)

    return render_template(
        "profile.html",
        customer=customer,
        reservations=reservations,
        vouchers=vouchers
    )

@app.route("/about")
def about_view():
    """About view: Comprehensive content about The Quest Hotel, hotel layout map, and offers."""
    return render_template("about.html")

# ==============================================================================
# AUTHENTICATION API ENDPOINTS
# ==============================================================================
@app.route("/api/login", methods=["POST"])
def api_login():
    """Authenticate customer by email or mobile number with 3-strike 60-second lockout."""
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    password = data.get("password", "").strip()
    client_ip = request.remote_addr or "127.0.0.1"

    if not identifier or not password:
        return jsonify({"success": False, "message": "Please enter your email or mobile number and password."}), 400

    success, customer, msg = authenticate_customer(identifier, password, client_ip)
    if success and customer:
        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["name"]
        return jsonify({
            "success": True,
            "message": f"Welcome back, {customer['name']}!",
            "customer": {
                "id": customer["id"],
                "name": customer["name"],
                "email": customer["email"],
                "loyalty_points": customer["loyalty_points"]
            }
        })
    else:
        # Check if currently locked out
        is_locked, secs_left = check_lockout(client_ip)
        return jsonify({
            "success": False,
            "message": msg,
            "is_locked": is_locked,
            "lockout_seconds": secs_left
        }), 401

@app.route("/api/social-login", methods=["POST"])
def api_social_login():
    """Simulated One-Click OAuth Login for Google and Facebook."""
    data = request.get_json() or {}
    provider = data.get("provider", "Google")
    social_id = data.get("social_id") or f"{provider.lower()}_{uuid.uuid4().hex[:10]}"
    email = data.get("email") or f"guest.{uuid.uuid4().hex[:6]}@example.com"
    name = data.get("name") or f"{provider} Guest"

    success, customer, msg = social_login(provider, social_id, email, name)
    if success and customer:
        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["name"]
        return jsonify({
            "success": True,
            "message": msg,
            "customer": {
                "id": customer["id"],
                "name": customer["name"],
                "email": customer["email"],
                "loyalty_points": customer["loyalty_points"]
            }
        })
    return jsonify({"success": False, "message": msg}), 400

@app.route("/api/register", methods=["POST"])
def api_register():
    """Register a new customer account with 100 welcome bonus points."""
    data = request.form if request.content_type and request.content_type.startswith("multipart/form-data") else (request.get_json() or {})
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    mobile_number = data.get("mobile_number", "").strip()
    password = data.get("password", "").strip()
    profile_image = request.files.get("profile_image")

    if not name or not password:
        return jsonify({"success": False, "message": "Please provide your full name and password."}), 400

    success, customer, msg = register_customer(name, email, mobile_number, password, profile_image)
    if success and customer:
        session["customer_id"] = customer["id"]
        session["customer_name"] = customer["name"]
        return jsonify({
            "success": True,
            "message": msg,
            "customer": {
                "id": customer["id"],
                "name": customer["name"],
                "email": customer["email"],
                "loyalty_points": customer["loyalty_points"]
            }
        })
    return jsonify({"success": False, "message": msg}), 400

@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    """Reset customer password by email or mobile number."""
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    new_password = data.get("new_password", "").strip()

    if not identifier or not new_password:
        return jsonify({"success": False, "message": "Please enter your email or mobile number and your new password."}), 400

    success, msg = reset_password(identifier, new_password)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)

@app.route("/api/logout", methods=["POST", "GET"])
def api_logout():
    """Log out current customer session."""
    session.clear()
    if request.method == "GET":
        return redirect(url_for("index"))
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route("/api/me")
def api_me():
    """Retrieve current logged in customer and active stay details."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"logged_in": False})

    customer = get_customer_by_id(customer_id)
    if not customer:
        session.clear()
        return jsonify({"logged_in": False})

    stay = get_active_stay(customer_id)
    return jsonify({
        "logged_in": True,
        "customer": {
            "id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "mobile_number": customer["mobile_number"],
            "loyalty_points": customer["loyalty_points"],
            "image_path": customer.get("image_path")
        },
        "active_stay": stay,
        "is_checked_in": stay is not None
    })

# ==============================================================================
# PROFILE RUD API ENDPOINTS
# ==============================================================================
@app.route("/api/profile/update", methods=["POST"])
def api_profile_update():
    """Update profile details (Name, Email, Mobile, optional password change)."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to update profile."}), 401

    data = request.form if request.content_type and request.content_type.startswith("multipart/form-data") else (request.get_json() or {})
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    mobile = data.get("mobile_number", "").strip()
    new_password = data.get("new_password", "").strip()
    profile_image = request.files.get("profile_image")

    if not name:
        return jsonify({"success": False, "message": "Name cannot be empty."}), 400
    image_error = validate_profile_image(profile_image)
    if image_error:
        return jsonify({"success": False, "message": image_error}), 400

    conn = get_connection()
    c = conn.cursor()
    try:
        # Check uniqueness of email if changing
        if email:
            c.execute("SELECT id FROM customers WHERE LOWER(email) = LOWER(?) AND id != ?", (email, customer_id))
            if c.fetchone():
                conn.close()
                return jsonify({"success": False, "message": "Email is already taken by another guest."}), 400

        # Check uniqueness of mobile if changing
        if mobile:
            c.execute("SELECT id FROM customers WHERE REPLACE(mobile_number, ' ', '') = ? AND id != ?", (mobile.replace(" ", ""), customer_id))
            if c.fetchone():
                conn.close()
                return jsonify({"success": False, "message": "Mobile number is already registered to another guest."}), 400

        if new_password:
            pwd_hash = hash_password(new_password)
            c.execute("""
                UPDATE customers SET name = ?, email = ?, mobile_number = ?, password_hash = ?
                WHERE id = ?
            """, (name, email, mobile, pwd_hash, customer_id))
        else:
            c.execute("""
                UPDATE customers SET name = ?, email = ?, mobile_number = ?
                WHERE id = ?
            """, (name, email, mobile, customer_id))

        conn.commit()
        image_path, image_error = store_profile_image(profile_image, customer_id)
        if image_error:
            conn.close()
            return jsonify({"success": False, "message": image_error}), 400
        if image_path:
            c.execute("UPDATE customers SET image_path = ? WHERE id = ?", (image_path, customer_id))
            conn.commit()
        conn.close()
        session["customer_name"] = name
        return jsonify({"success": True, "message": "Profile updated successfully!"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": f"Update failed: {str(e)}"}), 500

@app.route("/api/profile/connect-social", methods=["POST"])
def api_profile_connect_social():
    """Connect or disconnect Google / Facebook account."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    data = request.get_json() or {}
    provider = data.get("provider", "Google")
    action = data.get("action", "connect")  # connect or disconnect
    col = "google_id" if provider.lower() == "google" else "facebook_id"

    conn = get_connection()
    c = conn.cursor()
    if action == "disconnect":
        c.execute(f"UPDATE customers SET {col} = NULL WHERE id = ?", (customer_id,))
        msg = f"Disconnected {provider} account."
    else:
        new_val = f"{provider.lower()}_{uuid.uuid4().hex[:8]}"
        c.execute(f"UPDATE customers SET {col} = ? WHERE id = ?", (new_val, customer_id))
        msg = f"Connected {provider} account successfully!"
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": msg})

@app.route("/api/profile/delete", methods=["POST"])
def api_profile_delete():
    """Deactivate or remove customer account."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    conn = get_connection()
    c = conn.cursor()
    # Check if currently checked in
    c.execute("SELECT id FROM reservations WHERE customer_id = ? AND status = 'Checked In'", (customer_id,))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Cannot delete account while you have an active stay in the hotel."}), 400

    c.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    session.clear()
    return jsonify({"success": True, "message": "Your customer account has been deactivated. Thank you for staying with us."})

# ==============================================================================
# RESERVATION & EXTENSION API ENDPOINTS
# ==============================================================================
@app.route("/api/reservations/book", methods=["POST"])
def api_book_reservation():
    """Make a room reservation. Strictly requires logged-in customer."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({
            "success": False,
            "requires_login": True,
            "message": "Room reservations are exclusively for logged-in guests. Please sign in or register to complete your booking."
        }), 401

    data = request.get_json() or {}
    room_id = data.get("room_id")
    check_in = data.get("check_in_date")
    check_out = data.get("check_out_date")
    special_requests = data.get("special_requests", "")
    num_guests = int(data.get("num_guests", 1))

    if not room_id or not check_in or not check_out:
        return jsonify({"success": False, "message": "Please choose dates and suite."}), 400

    success, res_id, msg = create_reservation(
        customer_id=customer_id,
        room_id=room_id,
        check_in_date=check_in,
        check_out_date=check_out,
        special_requests=special_requests,
        num_guests=num_guests
    )

    return jsonify({"success": success, "reservation_id": res_id, "message": msg}), (200 if success else 400)

@app.route("/api/reservations/extend", methods=["POST"])
def api_extend_reservation():
    """Extend current checked-in reservation with payment calculation."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please log in to extend stay."}), 401

    data = request.get_json() or {}
    additional_days = int(data.get("additional_days", 1))
    payment_method = data.get("payment_method", "Credit Card")

    success, msg = extend_reservation(customer_id, additional_days, payment_method)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)

# ==============================================================================
# IN-STAY SERVICES & FOOD ORDERING API ENDPOINTS
# ==============================================================================
@app.route("/api/services/order-food", methods=["POST"])
def api_order_food():
    """Order in-room dining dishes. Requires guest to be checked in."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to place dining orders."}), 401

    stay = get_active_stay(customer_id)
    if not stay:
        return jsonify({
            "success": False,
            "message": "In-room dining is an exclusive in-stay privilege. You must be checked in to order food to your suite."
        }), 403

    data = request.get_json() or {}
    items = data.get("items", [])
    delivery_time = data.get("delivery_time", "As soon as ready (approx. 25-35 mins)")
    notes = data.get("notes", "")

    success, msg = create_food_order(
        customer_id=customer_id,
        room_id=stay["room_id"],
        items_json=items,
        delivery_time=delivery_time,
        notes=notes
    )

    return jsonify({"success": success, "message": msg}), (200 if success else 400)

@app.route("/api/services/book-service", methods=["POST"])
def api_book_service():
    """Book a hotel service (Massage, Laundry, Buffet, Car Rental). Requires checked-in guest."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to book services."}), 401

    stay = get_active_stay(customer_id)
    if not stay:
        return jsonify({
            "success": False,
            "message": "Hotel services are reserved for currently checked-in guests."
        }), 403

    data = request.get_json() or {}
    service_id = data.get("service_id")
    scheduled_time = data.get("scheduled_time", "Today - Afternoon")
    notes = data.get("notes", "")

    if not service_id:
        return jsonify({"success": False, "message": "Please choose a service."}), 400

    success, msg = create_service_booking(
        customer_id=customer_id,
        room_id=stay["room_id"],
        service_id=service_id,
        scheduled_time=scheduled_time,
        notes=notes
    )

    return jsonify({"success": success, "message": msg}), (200 if success else 400)

@app.route("/api/services/ridiculous-request", methods=["POST"])
def api_ridiculous_request():
    """Submit a bespoke custom request honoring the hotel oath."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to submit your request."}), 401

    stay = get_active_stay(customer_id)
    if not stay:
        return jsonify({
            "success": False,
            "message": "Custom ridiculous requests are exclusively handled for currently checked-in guests."
        }), 403

    data = request.get_json() or {}
    request_text = data.get("request_text", "").strip()

    success, msg = create_ridiculous_request(
        customer_id=customer_id,
        room_id=stay["room_id"],
        request_text=request_text
    )

    return jsonify({"success": success, "message": msg}), (200 if success else 400)

# ==============================================================================
# ASK QUESTIONS & CONCIERGE CHAT API ENDPOINTS
# ==============================================================================
@app.route("/api/ask/send", methods=["POST"])
def api_ask_send():
    """Send live inquiry to Front Desk or Concierge."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to communicate with front desk."}), 401

    stay = get_active_stay(customer_id)
    room_id = stay["room_id"] if stay else None

    data = request.get_json() or {}
    department = data.get("department", "Front Desk")
    message = data.get("message", "").strip()

    success, reply, msg = send_inquiry(customer_id, room_id, department, message)
    return jsonify({
        "success": success,
        "reply": reply,
        "message": msg
    }), (200 if success else 400)

@app.route("/api/ask/callback", methods=["POST"])
def api_ask_callback():
    """Request immediate phone call from front desk to suite or mobile."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to request callback."}), 401

    stay = get_active_stay(customer_id)
    room_id = stay["room_id"] if stay else None
    data = request.get_json() or {}
    phone = data.get("phone", "")
    notes = data.get("notes", "")

    success, msg = request_callback(customer_id, room_id, phone, notes)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)

# ==============================================================================
# LOYALTY REWARDS API ENDPOINTS
# ==============================================================================
@app.route("/api/rewards/redeem", methods=["POST"])
def api_redeem_reward():
    """Redeem customer loyalty points for reward vouchers."""
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"success": False, "message": "Please sign in to redeem rewards."}), 401

    data = request.get_json() or {}
    reward_id = data.get("reward_id")
    if not reward_id:
        return jsonify({"success": False, "message": "Please select a reward to redeem."}), 400

    success, voucher_code, msg = redeem_loyalty_reward(customer_id, int(reward_id))
    return jsonify({
        "success": success,
        "voucher_code": voucher_code,
        "message": msg
    }), (200 if success else 400)

# ==============================================================================
# APPLICATION ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    print(f"Starting The Quest Customer Website on http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
