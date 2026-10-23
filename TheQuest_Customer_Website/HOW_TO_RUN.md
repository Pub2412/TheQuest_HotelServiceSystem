# 🏨 The Quest Hotel - Customer Website: Quick Run Guide

> **Slogan:** *"We shall never deny a guest, even the most ridiculous request"*  
> **Brand Theme:** Royal Velvet Purple (`#3B185F`), Warm Amber Gold (`#F59E0B`), and Crisp White (`#FFFFFF`).

This guide details how to launch and run the **The Quest Hotel Customer Website** seamlessly on **Windows, macOS, or Linux** without requiring any external database configuration or server setup.

---

## ⚡ Method 1: One-Click Launch (Windows)

Simply double-click the included runner file inside `TheQuest_Customer_Website`:
```
run.bat
```
*This script will automatically detect your Python environment, verify the portable SQLite database, launch the local server, and open your web browser to `http://127.0.0.1:5000`.*

---

## 🐍 Method 2: Command Line (All Platforms: Windows, macOS, Linux)

### Step 1: Open Terminal / PowerShell
Open your terminal in the `TheQuest_Customer_Website` folder:
```bash
cd "c:\Users\Lancelot\Documents\School Files\Y3T1\ITElective1\Projects\FinalProject_Hotel_Service\TheQuest_Customer_Website"
```

### Step 2: Install Requirements (First Time Only)
```bash
pip install -r requirements.txt
```
*(Only requires lightweight `Flask` — uses Python's built-in `sqlite3` for zero setup!)*

### Step 3: Run the Portal
```bash
python run.py
```
*(Or `python app.py`)*

The system will display:
```
======================================================================
  THE QUEST HOTEL - CUSTOMER WEBSITE PORTAL
  "We shall never deny a guest, even the most ridiculous request"
======================================================================
[OK] Flask 3.0.3 is installed and ready.
[OK] SQLite Database located: database/hotel_service.db
[OK] Assets directory located: assets
[The Quest] Launching browser to http://127.0.0.1:5000 ...
[The Quest] Server online at http://127.0.0.1:5000
```
Then navigate to: **`http://127.0.0.1:5000`** in your browser.

---

## 🔑 Quick Demo Accounts for Testing

All seeded customer accounts share the default test password: **`Password123!`**

### 1. Actively Checked-In Customer (Explore Live Stay Timer & Room Service)
* **Name:** Amelia Watson  
* **Email:** `amelia.watson@gmail.com`  
* **Mobile:** `+63 919 111 0001`  
* **Password:** `Password123!`  
* **Features to Test:**  
  * Active stay banner with live countdown timer for **Suite 102**.
  * "Extend Reservation" button with instant checkout.
  * In-Room Dining ordering from the 25-item gourmet menu.
  * 24/7 Front Desk live chat & "Request Instant Desk Callback".

### 2. High-Roller VIP Customer (Explore Loyalty Rewards Redemption)
* **Name:** James Bond  
* **Email:** `james.bond@007.co.uk`  
* **Password:** `Password123!`  
* **Points Balance:** **2,100 pts (Royal Diamond Ambassador)**  
* **Features to Test:**  
  * Redeem the Presidential Penthouse Experience (2,000 pts) or Champagne Buffets.
  * Digital voucher generation and voucher wallet.

### 3. Non-Checked-In Customer (Explore Suite Reservations)
* **Name:** Luna Lovegood  
* **Email:** `luna.lovegood@hogwarts.edu`  
* **Password:** `Password123!`  
* **Features to Test:**  
  * Browse 17 room types with photos.
  * Book a suite with custom date calculations and "Ridiculous Request" text field.

### 4. New Guest Registration
* Click **"Guest Sign In" &rarr; "Register"** tab.
* Enter any Name, Email, Phone, and Password.
* Receive an automatic **100 Welcome Bonus Loyalty Points** upon registration!

---

## 🛡️ Security Features Tested
1. **3-Strike Login Lockout:**  
   Entering an incorrect password 3 consecutive times triggers a strict **60-second lockout** with an active countdown timer.
2. **PBKDF2 SHA-256 Hashing:**  
   Customer passwords use cryptographically secure salting and hashing fully compatible with the desktop management application.
3. **In-Stay Protection:**  
   In-room dining and desk callback services are strictly guarded so only currently checked-in guests can place orders to physical rooms.

---

## 📂 Portable Database Architecture
* The website connects directly to `database/hotel_service.db` using relative path traversal (`Path(__file__).resolve().parents[2] / 'database' / 'hotel_service.db'`).
* **Zero Absolute Paths:** The website will run flawlessly on any other computer or drive letter without path errors!
