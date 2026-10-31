"""
Hotel data services and database operations for The Quest Hotel Customer Mobile App.
Provides room types mapping, promotions, dining menu, hotel services,
reservations, stay extensions, and loyalty reward redemptions.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from .db import get_connection

# Room types mapped directly to images in assets/imgs/rooms/
ROOM_METADATA = {
    "Standard Ground King": {
        "category": "Standard Ground",
        "image": "assets/imgs/rooms/standard_ground_king.jpg",
        "default_price": 2500.0,
        "packs": 2,
        "floor": "Level 1 (Ground Level)",
        "bed": "1 King Bed",
        "size": "36 m²",
        "description": "Quiet, peaceful ground-floor sanctuary with a plush king-size bed, private garden terrace, and artisan amenities.",
        "amenities": ["King Bed", "Garden Terrace", "Rain Shower", "High-Speed Wi-Fi", "Espresso Machine", "24/7 Room Service"]
    },
    "Standard Ground Twin": {
        "category": "Standard Ground",
        "image": "assets/imgs/rooms/standard_ground_twin.jpg",
        "default_price": 2500.0,
        "packs": 2,
        "floor": "Level 1 (Ground Level)",
        "bed": "2 Twin Beds",
        "size": "36 m²",
        "description": "Comfortable ground-floor room featuring two twin beds with Egyptian cotton linens and direct garden access.",
        "amenities": ["Two Twin Beds", "Garden Access", "Smart HD TV", "High-Speed Wi-Fi", "Work Desk", "Artisan Bath Products"]
    },
    "Standard Ground Queen": {
        "category": "Standard Ground",
        "image": "assets/imgs/rooms/standard_ground_queen.jpg",
        "default_price": 2700.0,
        "packs": 2,
        "floor": "Level 1 (Ground Level)",
        "bed": "1 Queen Bed",
        "size": "38 m²",
        "description": "Elegant room equipped with a plush queen bed, warm ambient lighting, and quick ground access to courtyard.",
        "amenities": ["Queen Bed", "Courtyard View", "Deep Soak Tub", "High-Speed Wi-Fi", "Minibar", "In-Room Safe"]
    },
    "Deluxe Twin": {
        "category": "Deluxe",
        "image": "assets/imgs/rooms/deluxe_twin.jpg",
        "default_price": 3800.0,
        "packs": 2,
        "floor": "Level 2 (Guest Level)",
        "bed": "2 Twin Beds",
        "size": "42 m²",
        "description": "Spacious second-floor sanctuary with dual luxury beds, premium acoustic soundproofing, and courtyard vistas.",
        "amenities": ["Two Twin Beds", "City View", "Marble Bathroom", "High-Speed Wi-Fi", "Bose Soundbar", "Coffee Station"]
    },
    "Deluxe King": {
        "category": "Deluxe",
        "image": "assets/imgs/rooms/deluxe_king.jpg",
        "default_price": 3800.0,
        "packs": 2,
        "floor": "Level 2 (Guest Level)",
        "bed": "1 King Bed",
        "size": "44 m²",
        "description": "Refined guest room featuring an expansive California king bed, bespoke velvet seating, and garden architecture views.",
        "amenities": ["King Bed", "Lounge Seating", "Italian Marble Bath", "4K Smart TV", "Luxury Bathrobes", "Turndown Service"]
    },
    "Deluxe Queen": {
        "category": "Deluxe",
        "image": "assets/imgs/rooms/deluxe_queen.jpg",
        "default_price": 3800.0,
        "packs": 2,
        "floor": "Level 2 (Guest Level)",
        "bed": "1 Queen Bed",
        "size": "42 m²",
        "description": "Tastefully decorated suite with a plush queen bed, velvet chaise lounge, and soft mood lighting.",
        "amenities": ["Queen Bed", "Velvet Chaise", "Walk-in Shower", "High-Speed Wi-Fi", "Gourmet Tea Selection", "Mini Fridge"]
    },
    "Deluxe Balcony King": {
        "category": "Deluxe Balcony",
        "image": "assets/imgs/rooms/deluxe_balcony_king.jpeg",
        "default_price": 4500.0,
        "packs": 3,
        "floor": "Level 3 (Balcony Level)",
        "bed": "1 King Bed + Daybed",
        "size": "48 m²",
        "description": "Elevated third-floor living featuring a private open-air balcony, scenic skyline views, and opulent marble interiors.",
        "amenities": ["Private Balcony", "King Bed", "Daybed Lounge", "Skyline View", "Espresso Bar", "Complimentary Minibar"]
    },
    "Deluxe Balcony Twin": {
        "category": "Deluxe Balcony",
        "image": "assets/imgs/rooms/deluxe_balcony_twin.jpg",
        "default_price": 4500.0,
        "packs": 3,
        "floor": "Level 3 (Balcony Level)",
        "bed": "2 Twin Beds + Daybed",
        "size": "48 m²",
        "description": "Bright, airy balcony suite equipped with two twin beds and private terrace overlooking tropical hotel grounds.",
        "amenities": ["Private Balcony", "Two Twin Beds", "Terrace Seating", "High-Speed Wi-Fi", "Bluetooth Audio", "Luxury Linens"]
    },
    "Deluxe Balcony Queen": {
        "category": "Deluxe Balcony",
        "image": "assets/imgs/rooms/deluxe_balcony_queen.jpg",
        "default_price": 4500.0,
        "packs": 3,
        "floor": "Level 3 (Balcony Level)",
        "bed": "1 Queen Bed + Sofa Bed",
        "size": "48 m²",
        "description": "Breezy retreat with furnished private balcony for sunset viewing, queen bed, and rainfall shower ensuite.",
        "amenities": ["Sunset Balcony", "Queen Bed", "Rainfall Shower", "Smart 4K TV", "Cocktail Bar Kit", "Daily Fresh Fruit"]
    },
    "Executive Suite King": {
        "category": "Executive Suite",
        "image": "assets/imgs/rooms/executive_suite_king.jpg",
        "default_price": 6200.0,
        "packs": 4,
        "floor": "Level 4 (Executive Level)",
        "bed": "1 King Bed + Queen Sofa Bed",
        "size": "65 m²",
        "description": "Distinguished fourth-floor suite with separate parlor lounge, dedicated workstation, and Level 4 Lounge privileges.",
        "amenities": ["Separate Living Room", "King Bed", "Executive Desk", "Lounge Access", "Freestanding Tub", "Priority Concierge"]
    },
    "Executive Suite Twin": {
        "category": "Executive Suite",
        "image": "assets/imgs/rooms/executive_suite_twin.jpg",
        "default_price": 6200.0,
        "packs": 4,
        "floor": "Level 4 (Executive Level)",
        "bed": "2 Double Beds",
        "size": "65 m²",
        "description": "Expansive executive accommodation with dual luxury beds, dining table for four, and private conference access.",
        "amenities": ["Dining Area", "Two Double Beds", "City Skyline View", "Executive Lounge", "Nespresso Machine", "Shoeshine Service"]
    },
    "Executive Suite Queen": {
        "category": "Executive Suite",
        "image": "assets/imgs/rooms/executive_suite_queen.jpeg",
        "default_price": 6200.0,
        "packs": 4,
        "floor": "Level 4 (Executive Level)",
        "bed": "1 Queen Bed + Living Suite",
        "size": "62 m²",
        "description": "Sophisticated executive suite boasting custom wood furnishings, private wet bar, and deep soaking tub.",
        "amenities": ["Wet Bar", "Queen Bed", "Soaking Tub", "Complimentary Evening Canapés", "Lounge Privileges", "Fast Wi-Fi"]
    },
    "Penthouse Presidential Suite": {
        "category": "Penthouse & VIP",
        "image": "assets/imgs/rooms/penthouse_presidential_suite.jpg",
        "default_price": 9500.0,
        "packs": 6,
        "floor": "Level 5 (Presidential Penthouse)",
        "bed": "1 Master King + 1 Queen Guest",
        "size": "130 m²",
        "description": "Palatial luxury featuring 2 master bedrooms, grand salon, private dining room, and dedicated 24/7 personal butler.",
        "amenities": ["24/7 Personal Butler", "Two Master Bedrooms", "Private Dining Salon", "Jacuzzi Spa Bath", "Champagne on Arrival", "Chauffeur Transport"]
    },
    "Royal Panorama Suite": {
        "category": "Penthouse & VIP",
        "image": "assets/imgs/rooms/royal_panorama_suite.jpg",
        "default_price": 8500.0,
        "packs": 5,
        "floor": "Level 5 (Executive Level)",
        "bed": "1 Grand King + Living Salon",
        "size": "110 m²",
        "description": "Floor-to-ceiling glass delivering breathtaking 270-degree panorama views, grand piano, and luxury marble bar.",
        "amenities": ["270° Panoramic Views", "Grand Salon", "Marble Bar", "Designer Toiletries", "Private Wine Cellar", "VIP Airport Transfer"]
    },
    "Crown Luxury Suite": {
        "category": "Penthouse & VIP",
        "image": "assets/imgs/rooms/crown_luxury_suite.jpg",
        "default_price": 8500.0,
        "packs": 4,
        "floor": "Level 5 (Executive Level)",
        "bed": "1 King Bed + Luxury Lounge",
        "size": "100 m²",
        "description": "Imperial sanctuary appointed in royal violet and burnished gold with a freestanding marble jacuzzi and private balcony.",
        "amenities": ["Marble Jacuzzi", "Walk-in Wardrobe", "Private Terrace", "Evening Wine Service", "Dedicated Concierge", "Dyson Styling Kit"]
    },
    "Executive Horizon Suite": {
        "category": "Penthouse & VIP",
        "image": "assets/imgs/rooms/executive_horizon_suite.jpg",
        "default_price": 8000.0,
        "packs": 4,
        "floor": "Level 5 (Executive Level)",
        "bed": "1 King Bed + Study",
        "size": "95 m²",
        "description": "Commanding views overlooking the city horizon, with private study library, curated art, and butler call system.",
        "amenities": ["Private Library Study", "King Bed", "Butler Call System", "Soundproof Media Room", "Gourmet Pantry", "Limo Pickup"]
    },
    "Imperial Skylounge Suite": {
        "category": "Penthouse & VIP",
        "image": "assets/imgs/rooms/imperial_skylounge_suite.jpeg",
        "default_price": 9500.0,
        "packs": 6,
        "floor": "Level 5 (Presidential Penthouse)",
        "bed": "2 King Beds + Lounge",
        "size": "140 m²",
        "description": "Majestic residence directly connected to the private Imperial Skylounge, with terrace firepit and 24/7 butler.",
        "amenities": ["Private Terrace Firepit", "Skylounge Access", "Chef's Pantry", "Two King Suites", "Unlimited Spa Treatments", "24/7 Butler Service"]
    }
}

PROMOTIONS_DATA = [
    {
        "id": 1,
        "image": "assets/imgs/promotions/promo1.jpg",
        "badge": "Royal Sanctuary",
        "title": "Welcome to The Quest Experience",
        "subtitle": "Immerse yourself in opulent comfort where every desire is anticipatingly met.",
        "tagline": "We shall never deny a guest, even the most ridiculous request",
        "button_text": "Explore Suites",
        "button_link": "/rooms"
    },
    {
        "id": 2,
        "image": "assets/imgs/promotions/promo2.jpg",
        "badge": "Signature Privilege",
        "title": "Penthouse & Presidential Indulgence",
        "subtitle": "Enjoy 24/7 private white-glove butler service, chilled champagne, and skyline views.",
        "tagline": "We shall never deny a guest, even the most ridiculous request",
        "button_text": "View VIP Suites",
        "button_link": "/rooms?category=Penthouse+%26+VIP"
    },
    {
        "id": 3,
        "image": "assets/imgs/promotions/promo3.jpg",
        "badge": "Culinary Excellence",
        "title": "Bespoke 24/7 In-Room Dining",
        "subtitle": "From artisan seafood delicacies to midnight chocolate dreams delivered straight to your suite.",
        "tagline": "We shall never deny a guest, even the most ridiculous request",
        "button_text": "Explore In-Room Menu",
        "button_link": "/services"
    },
    {
        "id": 4,
        "image": "assets/imgs/promotions/promo4.jpg",
        "badge": "Wellness & Rejuvenation",
        "title": "The Royal Spa & Aromatherapy Retreat",
        "subtitle": "Restore mind and body with our master therapists and botanical healing treatments.",
        "tagline": "We shall never deny a guest, even the most ridiculous request",
        "button_text": "Discover Wellness",
        "button_link": "/services#services"
    }
]

def get_all_rooms(category_filter: Optional[str] = None) -> List[Dict]:
    """Retrieve all rooms enriched with metadata, images, and current availability."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT r.id, r.room_number, r.type, r.price_per_night, r.status,
               r.is_reserved, r.is_occupied, r.packs,
               COALESCE(r.wifi_ssid, 'Quest_Room_' || r.room_number) AS wifi_ssid,
               COALESCE(r.door_state, 'locked') AS door_state
        FROM rooms r
        ORDER BY CAST(r.room_number AS INTEGER), r.room_number
    """)
    rows = c.fetchall()
    conn.close()

    rooms = []
    for row in rows:
        room_dict = dict(row)
        meta = ROOM_METADATA.get(room_dict["type"], {})
        room_dict.update({
            "category": meta.get("category", "Suites"),
            "image": meta.get("image", "assets/imgs/rooms/standard_ground_king.jpg"),
            "floor": meta.get("floor", "Level 1"),
            "bed": meta.get("bed", "Luxury Bed"),
            "size": meta.get("size", "40 m²"),
            "description": meta.get("description", "Luxurious appointed guest room with first-class amenities."),
            "amenities": meta.get("amenities", ["Wi-Fi", "4K TV", "Ensuite Marble Bath", "Espresso Machine"])
        })
        is_available = (
            room_dict["is_occupied"] == 0
            and room_dict["is_reserved"] == 0
            and room_dict["status"] in ("Vacant", "Reserved")
        )
        room_dict["is_available"] = is_available
        room_dict["status_badge"] = (
            "Available" if is_available and room_dict["is_reserved"] == 0
            else ("Reserved" if room_dict["is_reserved"] == 1 else "Occupied")
        )

        if category_filter and category_filter != "All":
            if meta.get("category", "").lower() == category_filter.lower():
                rooms.append(room_dict)
        else:
            rooms.append(room_dict)

    return rooms

def get_room_by_id(room_id: int) -> Optional[Dict]:
    """Get single room details with full metadata."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT r.*,
               COALESCE(r.wifi_ssid, 'Quest_Room_' || r.room_number) AS wifi_ssid,
               COALESCE(r.door_state, 'locked') AS door_state
        FROM rooms r WHERE r.id = ?
    """, (room_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    r_dict = dict(row)
    meta = ROOM_METADATA.get(r_dict["type"], {})
    r_dict.update(meta)
    return r_dict

def create_reservation(customer_id: int, room_id: int, check_in_date: str, check_out_date: str,
                       special_requests: str = "", num_guests: int = 1) -> Tuple[bool, Optional[int], str]:
    """
    Create a new room reservation for a logged-in customer with all restrictions:
    - Logged-in check
    - Check-out date must be after check-in date
    - 2-hour turnover check (no overlapping Pending/Checked In stays)
    - If room currently occupied, check_in must be in future
    - Records revenue transaction & awards loyalty points (1 point per 100 PHP)
    """
    if not customer_id:
        return False, None, "Room reservations are exclusively for logged-in guests. Please sign in or register to complete your booking."

    try:
        d_in = datetime.strptime(check_in_date, "%Y-%m-%d").date()
        d_out = datetime.strptime(check_out_date, "%Y-%m-%d").date()
        if d_out <= d_in:
            return False, None, "Check-out date must be after check-in date."
        nights = (d_out - d_in).days
    except Exception:
        return False, None, "Invalid date format. Please use YYYY-MM-DD."

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return False, None, "Selected room was not found."

    room = dict(room)
    # Check turnover window: 12:00 PM checkout and 2:00 PM checkin
    c.execute("""
        SELECT id FROM reservations
        WHERE room_id = ? AND status IN ('Pending', 'Checked In')
        AND NOT (check_out_date <= ? OR check_in_date >= ?)
    """, (room_id, check_in_date, check_out_date))
    if c.fetchone():
        conn.close()
        return False, None, f"Room {room['room_number']} is unavailable for the chosen dates. Please choose dates with at least a two-hour turnover window."

    if room["is_occupied"] == 1 and d_in <= datetime.now().date():
        conn.close()
        return False, None, f"Room {room['room_number']} is currently occupied."

    total_amount = room["price_per_night"] * nights
    loyalty_pts_earned = int(total_amount // 100)

    try:
        c.execute("""
            INSERT INTO reservations (customer_id, room_id, check_in_date, check_out_date, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """, (customer_id, room_id, check_in_date, check_out_date))
        res_id = c.lastrowid

        c.execute("UPDATE rooms SET is_reserved = 1, status = 'Reserved' WHERE id = ?", (room_id,))

        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (
            total_amount,
            f"Reservation #{res_id}: Suite {room['room_number']} ({room['type']}) for {nights} nights. Special Request: '{special_requests}'",
            customer_id
        ))

        c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (loyalty_pts_earned, customer_id))

        if special_requests and special_requests.strip():
            c.execute("""
                INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
                VALUES (?, ?, 'Room Service', ?, 'Processing')
            """, (room_id, customer_id, f"Guest Ridiculous Request on Booking: {special_requests.strip()}"))

        conn.commit()
        conn.close()
        return True, res_id, f"Reservation confirmed for Suite {room['room_number']}! Total: ₱{total_amount:,.2f} ({nights} nights). You earned {loyalty_pts_earned} Loyalty Points!"
    except Exception as e:
        conn.close()
        return False, None, f"Reservation failed: {str(e)}"

def extend_reservation(customer_id: int, additional_days: int, payment_method: str = "Card") -> Tuple[bool, str]:
    """Extend a currently checked-in customer's stay with payment calculation."""
    if additional_days <= 0:
        return False, "Extension duration must be at least 1 night."

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT res.id, res.check_out_date, res.room_id, r.room_number, r.price_per_night, r.type
        FROM reservations res
        JOIN rooms r ON res.room_id = r.id
        WHERE res.customer_id = ? AND res.status = 'Checked In'
        ORDER BY res.id DESC LIMIT 1
    """, (customer_id,))
    stay = c.fetchone()
    if not stay:
        conn.close()
        return False, "You do not currently have an active checked-in stay to extend."

    stay = dict(stay)
    try:
        current_co = datetime.strptime(stay["check_out_date"], "%Y-%m-%d").date()
    except Exception:
        current_co = datetime.now().date()

    new_co = current_co + timedelta(days=additional_days)
    new_co_str = new_co.strftime("%Y-%m-%d")

    # Check that extension doesn't overlap future bookings
    c.execute("""
        SELECT id, check_in_date
        FROM reservations
        WHERE room_id = ? AND id <> ? AND status IN ('Pending', 'Checked In')
          AND check_in_date < ?
    """, (stay["room_id"], stay["id"], new_co_str))
    if c.fetchone():
        conn.close()
        return False, "Your extension would overlap a reserved stay. Please choose a shorter extension."

    cost = stay["price_per_night"] * additional_days
    earned_pts = int(cost // 100)

    try:
        c.execute("UPDATE reservations SET check_out_date = ? WHERE id = ?", (new_co_str, stay["id"]))
        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (cost, f"Stay Extension #{stay['id']} (+{additional_days} nights via {payment_method})", customer_id))
        c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (earned_pts, customer_id))
        conn.commit()
        conn.close()
        return True, f"Stay successfully extended by {additional_days} night(s) until {new_co_str}! Total charged: ₱{cost:,.2f} (+{earned_pts} loyalty points)."
    except Exception as e:
        conn.close()
        return False, f"Extension failed: {str(e)}"

def get_food_menu() -> List[Dict]:
    """Retrieve active food dishes for in-room dining."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, category, description, price, picture_link
        FROM fooditems
        WHERE is_active = 1
        ORDER BY category, name
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_hotel_services() -> List[Dict]:
    """Retrieve bookable hotel services."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, description, price, picture_link
        FROM service_list
        WHERE is_active = 1
        ORDER BY name
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_food_order(customer_id: int, room_id: int, items_json: List[Dict],
                      delivery_time: str, notes: str) -> Tuple[bool, str]:
    """Create in-room dining order (requires customer to be checked in)."""
    if not items_json:
        return False, "Your dining cart is empty."

    conn = get_connection()
    c = conn.cursor()

    order_lines = []
    total_cost = 0.0

    for item in items_json:
        item_id = item.get("id")
        qty = int(item.get("quantity", 1))
        c.execute("SELECT name, price FROM fooditems WHERE id = ?", (item_id,))
        dish = c.fetchone()
        if dish:
            subtotal = dish["price"] * qty
            total_cost += subtotal
            order_lines.append(f"{qty}x {dish['name']} (₱{subtotal:,.2f})")

    if not order_lines:
        conn.close()
        return False, "No valid dishes selected."

    summary = ", ".join(order_lines)
    details = f"In-Room Dining: {summary}. Est. Delivery: {delivery_time}. Notes: {notes or 'None'}"

    try:
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
            VALUES (?, ?, 'Food Delivery', ?, 'Processing')
        """, (room_id, customer_id, details))

        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (total_cost, f"Dining Order: {summary}", customer_id))

        pts = int(total_cost // 100)
        if pts > 0:
            c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (pts, customer_id))

        conn.commit()
        conn.close()
        return True, f"Order placed for Suite Room! Total: ₱{total_cost:,.2f}. Estimated delivery: {delivery_time}."
    except Exception as e:
        conn.close()
        return False, f"Failed to place dining order: {str(e)}"

def create_service_booking(customer_id: int, room_id: int, service_id: int,
                           scheduled_time: str, notes: str) -> Tuple[bool, str]:
    """Book a hotel service (Massage, Laundry, Buffet, Car Rental) for checked-in guest."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT name, price FROM service_list WHERE id = ?", (service_id,))
    svc = c.fetchone()
    if not svc:
        conn.close()
        return False, "Selected hotel service was not found."

    details = f"Service: {svc['name']} | Time: {scheduled_time} | Notes: {notes or 'None'}"

    try:
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, service_id, request_type, details, status)
            VALUES (?, ?, ?, 'Room Service', ?, 'Processing')
        """, (room_id, customer_id, service_id, details))

        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (svc["price"], f"Booked Service: {svc['name']} ({scheduled_time})", customer_id))

        pts = int(svc["price"] // 100)
        if pts > 0:
            c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (pts, customer_id))

        conn.commit()
        conn.close()
        return True, f"Booked '{svc['name']}'! Total: ₱{svc['price']:,.2f} added to room folio."
    except Exception as e:
        conn.close()
        return False, f"Service booking failed: {str(e)}"

def create_ridiculous_request(customer_id: int, room_id: int, request_text: str) -> Tuple[bool, str]:
    """Submit a bespoke request honoring hotel oath."""
    if not request_text or len(request_text.strip()) < 5:
        return False, "Please specify your request."

    conn = get_connection()
    c = conn.cursor()
    details = f"👑 RIDICULOUS REQUEST: \"{request_text.strip()}\""

    try:
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
            VALUES (?, ?, 'Room Service', ?, 'Processing')
        """, (room_id, customer_id, details))
        conn.commit()
        conn.close()
        return True, "Your request has been dispatched to Executive Butler team with Royal Oath priority!"
    except Exception as e:
        conn.close()
        return False, f"Submission failed: {str(e)}"

def get_loyalty_rewards() -> List[Dict]:
    """Get all redeemable loyalty rewards catalog."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, reward_name, points_required, description FROM loyalty_rewards ORDER BY points_required ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def redeem_loyalty_reward(customer_id: int, reward_id: int) -> Tuple[bool, Optional[str], str]:
    """Redeem customer points for reward voucher."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT loyalty_points FROM customers WHERE id = ?", (customer_id,))
    cust = c.fetchone()
    if not cust:
        conn.close()
        return False, None, "Customer not found."

    c.execute("SELECT reward_name, points_required FROM loyalty_rewards WHERE id = ?", (reward_id,))
    rew = c.fetchone()
    if not rew:
        conn.close()
        return False, None, "Reward not found."

    points = cust["loyalty_points"] or 0
    cost = rew["points_required"]

    if points < cost:
        conn.close()
        return False, None, f"Insufficient points. You have {points} pts, but this reward requires {cost} pts."

    code = f"QUEST-VOUCHER-{uuid.uuid4().hex[:8].upper()}"

    try:
        c.execute("UPDATE customers SET loyalty_points = loyalty_points - ? WHERE id = ?", (cost, customer_id))
        c.execute("""
            INSERT INTO redeemed_rewards (customer_id, reward_id, reward_name, points_spent, voucher_code, status)
            VALUES (?, ?, ?, ?, ?, 'Active')
        """, (customer_id, reward_id, rew["reward_name"], cost, code))
        conn.commit()
        conn.close()
        return True, code, f"Successfully redeemed '{rew['reward_name']}'! Voucher Code: {code}"
    except Exception as e:
        conn.close()
        return False, None, f"Redemption failed: {str(e)}"

def get_customer_vouchers(customer_id: int) -> List[Dict]:
    """Get list of active vouchers for customer."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, reward_name, points_spent, voucher_code, status, date_redeemed
        FROM redeemed_rewards
        WHERE customer_id = ?
        ORDER BY id DESC
    """, (customer_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_reservations(customer_id: int) -> List[Dict]:
    """Retrieve full booking history for customer."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT res.id, res.check_in_date, res.check_out_date, res.status,
               r.room_number, r.type AS room_type, r.price_per_night,
               COALESCE(r.wifi_ssid, 'Quest_Room_' || r.room_number) AS wifi_ssid,
               COALESCE(r.door_state, 'locked') AS door_state
        FROM reservations res
        JOIN rooms r ON res.room_id = r.id
        WHERE res.customer_id = ?
        ORDER BY res.id DESC
    """, (customer_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def send_inquiry(customer_id: int, room_id: Optional[int], department: str, message: str) -> Tuple[bool, str, str]:
    """Send live inquiry to Front Desk / Concierge with automated acknowledgement."""
    if not message or len(message.strip()) < 3:
        return False, "", "Please enter a message."

    conn = get_connection()
    c = conn.cursor()

    dept_replies = {
        "Front Desk": "Thank you for reaching out to Front Desk! A Guest Services Associate is attending to your request.",
        "Concierge": "Greetings from The Quest Concierge! Our team is curating bespoke assistance for your stay.",
        "Housekeeping": "Housekeeping has received your inquiry and our floor attendant has been notified.",
        "Room Service": "Kitchen & In-Room Dining team received your message. Bon appétit!"
    }
    auto_reply = dept_replies.get(department, "Thank you for reaching out. We are attending to your request immediately.")

    try:
        c.execute("""
            INSERT INTO customer_inquiries (customer_id, room_id, department, sender_type, message, response, status)
            VALUES (?, ?, ?, 'Customer', ?, ?, 'Answered')
        """, (customer_id, room_id, department, message.strip(), auto_reply))
        conn.commit()
        conn.close()
        return True, auto_reply, "Inquiry dispatched to staff."
    except Exception as e:
        conn.close()
        return False, "", f"Message failed: {str(e)}"

def request_callback(customer_id: int, room_id: Optional[int], phone: str, notes: str) -> Tuple[bool, str]:
    """Request an immediate phone call from front desk."""
    conn = get_connection()
    c = conn.cursor()
    msg = f"CALL REQUEST: Please ring {phone}. Notes: {notes or 'Immediate assistance needed'}"
    try:
        c.execute("""
            INSERT INTO customer_inquiries (customer_id, room_id, department, sender_type, message, response, status)
            VALUES (?, ?, 'Front Desk', 'Customer', ?, 'Front desk phone callback scheduled immediately.', 'Answered')
        """, (customer_id, room_id, msg))
        conn.commit()
        conn.close()
        return True, f"Front desk will phone you at {phone} within 2-3 minutes."
    except Exception as e:
        conn.close()
        return False, f"Callback request failed: {str(e)}"

def get_inquiries_history(customer_id: int) -> List[Dict]:
    """Retrieve chat history between guest and hotel desk."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, room_id, department, sender_type, message, response, status, created_at
        FROM customer_inquiries
        WHERE customer_id = ?
        ORDER BY id ASC
    """, (customer_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

