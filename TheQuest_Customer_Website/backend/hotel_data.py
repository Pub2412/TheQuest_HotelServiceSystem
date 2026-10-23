"""
Hotel data services and database operations for The Quest Hotel Customer Website.
Provides room types mapping, promotional carousel data, menu fetching,
reservations, stay extensions, service requests, and loyalty redemptions.
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
        "description": "Quiet, peaceful ground-floor sanctuary with a plush king-size bed, private garden view terrace, and bespoke artisan amenities.",
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
        "description": "Comfortable ground-floor room featuring two twin beds with Egyptian cotton linens, direct garden access, and modern luxury comforts.",
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
        "description": "Elegant room equipped with a plush queen bed, warm ambient lighting, and quick ground access to our courtyard and restaurant.",
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
        "description": "Spacious second-floor sanctuary with dual luxury beds, premium acoustic soundproofing, and panoramic courtyard vistas.",
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
        "description": "A refined guest room featuring an expansive California king bed, bespoke velvet seating, and sweeping garden architecture views.",
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
        "description": "Tastefully decorated suite with a plush queen bed, velvet chaise lounge, and soft mood lighting for restorative relaxation.",
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
        "description": "Elevated third-floor living featuring a private open-air balcony, scenic skyline views, and opulent marble-finished interiors.",
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
        "description": "Bright, airy balcony suite equipped with two twin beds and a private terrace overlooking the lush tropical hotel grounds.",
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
        "description": "A breezy retreat with a furnished private balcony for sunset viewing, queen bed, and luxury ensuite bathroom with rainfall shower.",
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
        "description": "Distinguished fourth-floor suite with separate parlor lounge, dedicated executive workstation, and exclusive Level 4 Lounge privileges.",
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
        "description": "Expansive executive accommodation with dual luxury beds, dining table for four, and full access to private conference facilities.",
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
        "description": "Sophisticated executive suite boasting custom wood furnishings, private wet bar, deep soaking tub, and evening cocktail reception.",
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
        "description": "The pinnacle of royal indulgence. 130 m² of palatial luxury featuring 2 master bedrooms, grand salon, private dining room, and dedicated 24/7 personal butler.",
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
        "description": "Floor-to-ceiling glass wrapping around the 5th floor, delivering breathtaking 270-degree panorama views, grand piano, and luxury marble bar.",
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
        "description": "An imperial sanctuary appointed in royal violet and burnished gold with a freestanding marble jacuzzi, walk-in dressing salon, and private balcony.",
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
        "description": "Commanding horizon views overlooking the horizon, complete with private study library, curated contemporary art, and bespoke butler call system.",
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
        "description": "Our most majestic residence directly connected to the private Imperial Skylounge, with private terrace firepit, chef's pantry, and limitless pampering.",
        "amenities": ["Private Terrace Firepit", "Skylounge Access", "Chef's Pantry", "Two King Suites", "Unlimited Spa Treatments", "24/7 Butler Service"]
    }
}

# Promotional Carousel Data using images from assets/imgs/promotions/
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
        "button_link": "/services#hotel-services"
    }
]

def get_all_rooms(category_filter: Optional[str] = None) -> List[Dict]:
    """Retrieve all rooms from the database enriched with metadata, images, and current availability."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, room_number, type, price_per_night, status, is_reserved, is_occupied, packs
        FROM rooms
        ORDER BY room_number ASC
    """)
    rows = c.fetchall()
    conn.close()

    rooms = []
    for r in rows:
        room_dict = dict(r)
        rtype = room_dict["type"]
        meta = ROOM_METADATA.get(rtype, {
            "category": "Standard",
            "image": "assets/imgs/rooms/standard_ground_king.jpg",
            "default_price": room_dict["price_per_night"],
            "packs": room_dict["packs"],
            "floor": "Guest Floor",
            "bed": "1 King Bed",
            "size": "40 m²",
            "description": f"Luxurious {rtype} at The Quest Hotel.",
            "amenities": ["High-Speed Wi-Fi", "Room Service", "Smart TV", "Luxury Bath"]
        })
        room_dict.update(meta)
        # Determine real-time booking availability
        # Available if not occupied and not reserved
        is_available = (room_dict["is_occupied"] == 0 and room_dict["is_reserved"] == 0 and room_dict["status"] == "Vacant")
        room_dict["is_available"] = is_available
        room_dict["status_badge"] = "Available" if is_available else ("Occupied" if room_dict["is_occupied"] == 1 else "Reserved")

        if category_filter:
            if meta.get("category", "").lower() == category_filter.lower():
                rooms.append(room_dict)
        else:
            rooms.append(room_dict)

    return rooms

def get_room_by_id(room_id: int) -> Optional[Dict]:
    """Get single room details with full metadata."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
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
    Create a new room reservation for a logged-in customer.
    Validates room availability, dates, creates reservation, records transaction, and awards loyalty points.
    """
    if not customer_id:
        return False, None, "You must be signed in to reserve a room."

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

    # Check room exists
    c.execute("SELECT * FROM rooms WHERE id = ?", (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return False, None, "Selected room was not found."

    room = dict(room)
    # Check if currently reserved or occupied
    if room["is_occupied"] == 1 or room["is_reserved"] == 1:
        # Check if there is an active reservation overlapping
        c.execute("""
            SELECT id FROM reservations 
            WHERE room_id = ? AND status IN ('Pending', 'Checked In')
            AND NOT (check_out_date <= ? OR check_in_date >= ?)
        """, (room_id, check_in_date, check_out_date))
        if c.fetchone():
            conn.close()
            return False, None, f"Room {room['room_number']} is currently unavailable for the chosen dates."

    total_amount = room["price_per_night"] * nights
    loyalty_pts_earned = int(total_amount // 100)  # 1 point per 100 PHP spent

    try:
        # 1. Insert reservation
        c.execute("""
            INSERT INTO reservations (customer_id, room_id, check_in_date, check_out_date, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """, (customer_id, room_id, check_in_date, check_out_date))
        res_id = c.lastrowid

        # 2. Update room status to reserved
        c.execute("UPDATE rooms SET is_reserved = 1, status = 'Reserved' WHERE id = ?", (room_id,))

        # 3. Insert transaction
        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (
            total_amount,
            f"Reservation #{res_id}: Suite {room['room_number']} ({room['type']}) for {nights} nights. Special Request: '{special_requests}'",
            customer_id
        ))

        # 4. Award loyalty points to customer
        c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (loyalty_pts_earned, customer_id))

        # 5. If special / ridiculous request provided, record into service_requests for staff attention
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
    """
    Extend a currently checked-in customer's stay with payment calculation.
    Updates reservations.check_out_date, logs transaction, and adds loyalty points.
    """
    if additional_days <= 0:
        return False, "Extension duration must be at least 1 night."

    conn = get_connection()
    c = conn.cursor()

    # Find active checked-in reservation
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
    cost = stay["price_per_night"] * additional_days
    earned_pts = int(cost // 100)

    try:
        # Update checkout date
        c.execute("UPDATE reservations SET check_out_date = ? WHERE id = ?", (new_co_str, stay["id"]))

        # Log revenue transaction
        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (
            cost,
            f"Stay Extension: Suite {stay['room_number']} extended by {additional_days} night(s) to {new_co_str}. Paid via {payment_method}.",
            customer_id
        ))

        # Award loyalty points
        c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (earned_pts, customer_id))

        conn.commit()
        conn.close()
        return True, f"Your stay in Suite {stay['room_number']} has been extended to {new_co_str} (+{additional_days} night(s)). Total charged: ₱{cost:,.2f} via {payment_method}. You earned {earned_pts} loyalty points!"
    except Exception as e:
        conn.close()
        return False, f"Failed to extend reservation: {str(e)}"

def get_food_menu() -> Dict[str, List[Dict]]:
    """Retrieve all 25 active food items grouped by category with image paths."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, category, description, price, picture_link
        FROM fooditems
        WHERE is_active = 1
        ORDER BY category ASC, id ASC
    """)
    rows = c.fetchall()
    conn.close()

    grouped = {}
    for r in rows:
        item = dict(r)
        # Ensure image path exists or fallback
        img = item.get("picture_link") or ""
        if not img or not img.startswith("assets/"):
            # Clean name for image match
            clean = item["name"].lower().replace(" ", "_").replace("-", "_") + ".jpg"
            img = f"assets/imgs/foodmenu/{clean}"
        item["image"] = img
        cat = item["category"] or "Specialties"
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(item)

    return grouped

def get_hotel_services() -> List[Dict]:
    """Retrieve all 8 hotel services with photos and pricing."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, description, price, picture_link
        FROM service_list
        WHERE is_active = 1
        ORDER BY id ASC
    """)
    rows = c.fetchall()
    conn.close()

    services = []
    for r in rows:
        s = dict(r)
        img = s.get("picture_link") or ""
        if not img or not img.startswith("assets/"):
            img = "assets/imgs/serv/massage.jpg"
        s["image"] = img
        services.append(s)

    return services

def create_food_order(customer_id: int, room_id: int, items_json: List[Dict], delivery_time: str, notes: str) -> Tuple[bool, str]:
    """
    Submit a room service food order for a checked-in guest.
    Inserts into service_requests table (request_type='Food Delivery').
    """
    if not items_json:
        return False, "Your dining cart is empty."

    total_amount = 0.0
    item_summaries = []
    for it in items_json:
        qty = int(it.get("quantity", 1))
        price = float(it.get("price", 0.0))
        name = it.get("name", "Dish")
        total_amount += (price * qty)
        item_summaries.append(f"{qty}x {name}")

    details = f"Dishes: {', '.join(item_summaries)} | Delivery: {delivery_time} | Notes: {notes or 'None'}"

    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
            VALUES (?, ?, 'Food Delivery', ?, 'Processing')
        """, (room_id, customer_id, details))
        req_id = c.lastrowid

        # Record transaction
        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (total_amount, f"In-Room Dining Order #{req_id}: {', '.join(item_summaries)}", customer_id))

        # Award loyalty points
        earned_pts = int(total_amount // 100)
        if earned_pts > 0:
            c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (earned_pts, customer_id))

        conn.commit()
        conn.close()
        return True, f"Your in-room dining order #{req_id} has been transmitted to Chef Marcus and culinary staff! Total: ₱{total_amount:,.2f} (Charged to Room Bill)."
    except Exception as e:
        conn.close()
        return False, f"Failed to submit food order: {str(e)}"

def create_service_booking(customer_id: int, room_id: int, service_id: int, scheduled_time: str, notes: str) -> Tuple[bool, str]:
    """
    Book a hotel service (Massage, Laundry, Buffet, Car Rental) for checked-in guest.
    Inserts into service_requests (request_type='Room Service').
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM service_list WHERE id = ?", (service_id,))
    s_row = c.fetchone()
    if not s_row:
        conn.close()
        return False, "Selected service was not found."

    s_row = dict(s_row)
    details = f"{s_row['name']} scheduled for {scheduled_time}. Instructions: {notes or 'Standard delivery'}"

    try:
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, service_id, request_type, details, status)
            VALUES (?, ?, ?, 'Room Service', ?, 'Processing')
        """, (room_id, customer_id, service_id, details))
        req_id = c.lastrowid

        # Record transaction
        c.execute("""
            INSERT INTO transactions (type, amount, description, customer_id)
            VALUES ('Revenue', ?, ?, ?)
        """, (s_row["price"], f"Hotel Service #{req_id}: {s_row['name']}", customer_id))

        # Award points
        earned_pts = int(s_row["price"] // 100)
        if earned_pts > 0:
            c.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (earned_pts, customer_id))

        conn.commit()
        conn.close()
        return True, f"Service '{s_row['name']}' booked successfully! Scheduled for {scheduled_time}. Request #{req_id} is now processing."
    except Exception as e:
        conn.close()
        return False, f"Failed to book service: {str(e)}"

def create_ridiculous_request(customer_id: int, room_id: int, request_text: str) -> Tuple[bool, str]:
    """
    Submit a custom bespoke request honoring the hotel oath:
    'We shall never deny a guest, even the most ridiculous request.'
    """
    if not request_text or len(request_text.strip()) < 5:
        return False, "Please specify your request details so our concierge can prepare it."

    conn = get_connection()
    c = conn.cursor()
    details = f"[THE RIDICULOUS REQUEST CONCIERGE]: {request_text.strip()}"
    try:
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
            VALUES (?, ?, 'Room Service', ?, 'Processing')
        """, (room_id, customer_id, details))
        req_id = c.lastrowid
        conn.commit()
        conn.close()
        return True, f"Request #{req_id} accepted! As per our sacred oath — 'We shall never deny a guest, even the most ridiculous request' — our concierge team has begun coordinating your request immediately."
    except Exception as e:
        conn.close()
        return False, f"Submission error: {str(e)}"

def get_loyalty_rewards() -> List[Dict]:
    """Retrieve all available loyalty rewards from database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM loyalty_rewards ORDER BY points_required ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def redeem_loyalty_reward(customer_id: int, reward_id: int) -> Tuple[bool, Optional[str], str]:
    """
    Redeem loyalty points for a reward voucher.
    Checks customer points balance, deducts points, and creates digital voucher code.
    """
    conn = get_connection()
    c = conn.cursor()

    # Get customer points
    c.execute("SELECT loyalty_points, name FROM customers WHERE id = ?", (customer_id,))
    cust = c.fetchone()
    if not cust:
        conn.close()
        return False, None, "Customer account not found."

    pts = cust["loyalty_points"] or 0

    # Get reward details
    c.execute("SELECT * FROM loyalty_rewards WHERE id = ?", (reward_id,))
    rew = c.fetchone()
    if not rew:
        conn.close()
        return False, None, "Reward option not found."

    rew = dict(rew)
    req_pts = rew["points_required"]
    if pts < req_pts:
        conn.close()
        return False, None, f"Insufficient loyalty points. You have {pts} points, but this reward requires {req_pts} points."

    # Deduct points & generate voucher
    voucher_code = f"QUEST-REW-{uuid.uuid4().hex[:8].upper()}"
    try:
        c.execute("UPDATE customers SET loyalty_points = loyalty_points - ? WHERE id = ?", (req_pts, customer_id))
        c.execute("""
            INSERT INTO redeemed_rewards (customer_id, reward_id, reward_name, points_spent, voucher_code, status)
            VALUES (?, ?, ?, ?, ?, 'Active')
        """, (customer_id, reward_id, rew["reward_name"], req_pts, voucher_code))
        conn.commit()
        conn.close()
        return True, voucher_code, f"Congratulations! You redeemed '{rew['reward_name']}' for {req_pts} points. Your voucher code is {voucher_code}."
    except Exception as e:
        conn.close()
        return False, None, f"Redemption failed: {str(e)}"

def get_customer_vouchers(customer_id: int) -> List[Dict]:
    """Get list of active or redeemed vouchers for a customer."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM redeemed_rewards
        WHERE customer_id = ?
        ORDER BY id DESC
    """, (customer_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_reservations(customer_id: int) -> List[Dict]:
    """Get all past and present reservations for a customer."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT res.id, res.check_in_date, res.check_out_date, res.status,
               r.room_number, r.type AS room_type, r.price_per_night
        FROM reservations res
        JOIN rooms r ON res.room_id = r.id
        WHERE res.customer_id = ?
        ORDER BY res.id DESC
    """, (customer_id,))
    rows = c.fetchall()
    conn.close()

    res_list = []
    for r in rows:
        d = dict(r)
        meta = ROOM_METADATA.get(d["room_type"], {})
        d["image"] = meta.get("image", "assets/imgs/rooms/standard_ground_king.jpg")
        res_list.append(d)
    return res_list

def send_inquiry(customer_id: int, room_id: Optional[int], department: str, message: str) -> Tuple[bool, str, str]:
    """
    Send an inquiry / chat message to Front Desk or Concierge.
    Generates a courteous 5-star hotel concierge automated acknowledgement reply.
    """
    if not message or len(message.strip()) == 0:
        return False, "", "Please enter a message to send."

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
    cust_row = c.fetchone()
    guest_name = cust_row["name"] if cust_row else "Esteemed Guest"

    # Courteous automated reply
    reply = f"Certainly, {guest_name}! Your message has been received by our {department} team. An attendant is reviewing your request immediately and will attend to your suite shortly."

    try:
        c.execute("""
            INSERT INTO customer_inquiries (customer_id, room_id, department, sender_type, message, response, status)
            VALUES (?, ?, ?, 'Customer', ?, ?, 'Answered')
        """, (customer_id, room_id, department, message.strip(), reply))
        conn.commit()
        conn.close()
        return True, reply, "Message delivered to Front Desk."
    except Exception as e:
        conn.close()
        return False, "", f"Message failed: {str(e)}"

def request_callback(customer_id: int, room_id: Optional[int], phone: str, notes: str) -> Tuple[bool, str]:
    """Request an immediate phone callback to room or mobile from front desk."""
    conn = get_connection()
    c = conn.cursor()
    try:
        # Insert into service requests as urgent callback
        detail_msg = f"URGENT DESK CALLBACK REQUEST: Guest requested phone call to {phone or 'Room Phone'}. Notes: {notes or 'Immediate assistance'}"
        c.execute("""
            INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
            VALUES (?, ?, 'Room Service', ?, 'Processing')
        """, (room_id, customer_id, detail_msg))

        # Also log in inquiries
        c.execute("""
            INSERT INTO customer_inquiries (customer_id, room_id, department, sender_type, message, response, status)
            VALUES (?, ?, 'Front Desk', 'Customer', ?, 'Front desk callback dispatched. Expected ring time < 2 minutes.', 'Answered')
        """, (customer_id, room_id, f"Requested callback to: {phone}"))

        conn.commit()
        conn.close()
        return True, "Front desk callback requested! A concierge agent will phone your suite/mobile within 60 to 120 seconds."
    except Exception as e:
        conn.close()
        return False, f"Callback request failed: {str(e)}"

def get_inquiries_history(customer_id: int) -> List[Dict]:
    """Get message thread history for customer."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM customer_inquiries
        WHERE customer_id = ?
        ORDER BY id ASC
    """, (customer_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
