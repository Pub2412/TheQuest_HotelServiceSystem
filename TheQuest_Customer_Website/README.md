# 👑 The Quest Hotel — Customer Website Portal

> *"We shall never deny a guest, even the most ridiculous request"*

An ultra-luxury 5-star customer web portal engineered for **The Quest Hotel & Residences**. Built with high-end royal purple and warm amber gold aesthetics matching the desktop application, enriched with modern responsive glassmorphism, smooth animations, and comprehensive guest services.

---

## 🌟 Key Functional Features (Based on `func-rec.txt`)

### 1. 🔑 Multi-Channel Authentication & Security Lockout
* **Login Methods:** Supports Email, Mobile Number, or Simulated One-Click Google and Facebook OAuth.
* **Security 3-Strike Lockout:** Exactly as specified in the functional requirements, 3 consecutive failed attempts trigger an automatic **60-second system lockout** with an active live countdown.
* **Password Hashing:** Fully integrated with PBKDF2 SHA-256 (`salt$hash`) matching the core SQLite database.
* **Guest Registration & Forgot Password:** New guests receive **100 welcome loyalty points** upon signing up.

### 2. 🏛️ Home View & Promotional Carousel
* **Auto/Manual Carousel:** Features the 4 high-resolution promotional assets from `assets/imgs/promotions/` (`promo1.jpg` to `promo4.jpg`) with automatic 5-second transitions, gold chevron controls, and clickable indicator dots.
* **Live In-Stay Residence Widget:**
  * When a customer is checked in, the home page dynamically transforms to display their active Suite Number, Suite Type, and Check-in/Check-out dates.
  * Real-time ticking countdown showing days, hours, minutes, and seconds remaining on their stay.
  * Reservation card automatically adapts to **"Extend Reservation"**.
* **Quick Access Navigation Tiles:** 6 curated luxury tiles directing to Profile, Reservations, Ask Concierge, Request Service, Loyalty Rewards, and About.
* **The Sacred Oath Showcase:** Emphasizes the hotel creed: *"We shall never deny a guest, even the most ridiculous request"*.

### 3. 🛌 Make Reservation & Extend Reservation View
* **Reservations are for Logged-In Customers Only:** Visitors are prompted to sign in before booking.
* **Full Room Catalog:** All 17 room types from `assets/data/room_types.txt` mapped to their photos from `assets/imgs/rooms/`.
* **Category Filters:** Filter by Standard Ground, Deluxe, Deluxe Balcony, Executive Suite, and Penthouse & VIP Suites.
* **Interactive Booking Calculator:** Date pickers dynamically calculate total nights and total PHP price.
* **"The Ridiculous Request" Input:** Dedicated booking field for extravagant guest requests.
* **Extend Stay Feature:** Checked-in guests can extend their stay by 1 to 7 nights with payment simulation (Room Folio Charge, Saved Card, GCash, Maya).

### 4. 🍽️ In-Stay Services & Dining Menu
* **Gourmet Room Service (25 Food Items):** Sourced from the `fooditems` database table, categorized by Appetizers, Mains, Breakfast, Desserts, and Beverages with photos from `assets/imgs/foodmenu/`.
* **Interactive Dining Cart:** Real-time subtotal, quantity adjustment, dietary requests, and delivery time options.
* **Hotel Services (8 Services):** Body Massage, Laundry, Minibar Restocking, Car Rental, and Buffets with photos from `assets/imgs/serv/`.
* **"The Ridiculous Request" Concierge:** A dedicated bespoke builder for custom desires honoring the hotel oath.

### 5. 🛎️ Ask Questions & Concierge Live Desk
* **Checked-In Guest Portal:** Direct real-time messaging with Front Desk, Chief Concierge, Housekeeping, Dining, and Duty Manager.
* **Automated Courteous Receptionist:** Instant 5-star acknowledgement replies for all guest inquiries.
* **"Request Instant Desk Callback":** Dispatches an urgent front desk phone call to the suite within 60 seconds.
* **Hotel Telephone Directory:** Quick reference to hotel extensions (0, 1, 2, 3, 4).

### 6. 💎 Loyalty Rewards Club
* **Live Points Balance & VIP Tier:** Displays Silver, Gold VIP (500 pts), Platinum Elite (1,000 pts), and Royal Diamond Ambassador (2,000 pts).
* **Rewards Catalog:** Sourced from `loyalty_rewards` database table.
* **Instant Digital Voucher Redemption:** Deducts points, generates unique codes (`QUEST-REW-XXXXX`), and saves to the guest's voucher wallet.

### 7. 👤 Guest Profile RUD View
* **Read:** View personal information, avatar, tier, points, and full reservation history.
* **Update:** Edit name, email, mobile number, and password.
* **Delete:** Option to deactivate customer account.
* **Social Accounts:** Connect or disconnect Google and Facebook accounts.

### 8. 🗺️ About The Quest & Architectural Hotel Map
* Comprehensive history, guest guidelines, and the story of the sacred oath.
* Interactive architectural cross-section floorplan map featuring `assets/imgs/HotelMap.jpg`.

---

## 💻 How to Run

1. Open `TheQuest_Customer_Website` folder.
2. Double-click `run.bat` (Windows), or execute:
   ```bash
   pip install -r requirements.txt
   python run.py
   ```
3. The server starts at `http://127.0.0.1:5000` and automatically opens in your default browser.

---

## 📁 Project Structure

```
TheQuest_Customer_Website/
├── app.py                     # Main Flask application & routes
├── run.py                     # Launcher script with auto-browser opening
├── run.bat                    # One-click Windows runner
├── requirements.txt           # Dependencies (Flask)
├── README.md                  # System overview & features
├── HOW_TO_RUN.md              # Detailed running guide & demo accounts
├── backend/
│   ├── __init__.py
│   ├── db.py                  # Portable SQLite database connector
│   ├── auth.py                # 3-strike lockout, PBKDF2 hashing, social login
│   └── hotel_data.py          # Room metadata, menu, services, reservations, rewards
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Ultra-luxury purple & gold design system
│   │   └── js/
│   │       └── main.js        # Carousel, stay countdown, cart, booking, chat
│   └── templates/
│       ├── base.html          # Global layout, modals, stay bar, footer
│       ├── index.html         # Home view with carousel & stay widget
│       ├── rooms.html         # Make / extend reservation view
│       ├── services.html      # Food menu, services & ridiculous request
│       ├── ask.html           # Concierge chat & callback
│       ├── rewards.html       # Loyalty rewards catalog & redemption
│       ├── profile.html       # Profile RUD, social accounts, history
│       └── about.html         # Hotel heritage & architectural map
└── logs/
```
