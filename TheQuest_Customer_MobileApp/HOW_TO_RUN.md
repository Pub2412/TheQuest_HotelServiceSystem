# The Quest Hotel - Customer Mobile Application

This application is the mobile port of `TheQuest_Customer_Website` tailored for smartphone form factors, mobile WebViews, and Android deployment.

## Features

1. **Digital Keycard & Smart Door Lock Access**:
   - Contactless **Wi-Fi proximity door unlock**: unlocked only when device is connected to the suite's matching Wi-Fi network.
   - Contactless **NFC tap door unlock**: simulates high-frequency NFC key beam to open the door instantly with auto-relocking safety after 5 seconds.
   - Regular room keys are uniquely generated and securely hashed (SHA-256) upon check-in, and automatically revoked on checkout.
2. **Real-Time Stay Countdown Clock**:
   - Shows active suite number, room type, and live remaining stay duration (days, hours, minutes, seconds).
3. **Restricted In-Stay Services & Dining**:
   - In-room dining ordering and hotel amenity bookings (spa, laundry, executive rental) are reserved for currently checked-in guests.
   - Includes "The Ridiculous Request Oath" form honoring the hotel oath.
4. **Interactive Front Desk Concierge**:
   - Multi-department messaging and urgent phone callback requests.
5. **Loyalty Rewards & Voucher Catalog**:
   - Earn 1 point per ₱100 spent. Instant voucher redemptions.
6. **Security & Authentication**:
   - Email and mobile number login, 3-strike 60-second security lockout.
   - One-click Google and Facebook simulated OAuth login.
   - Profile management, image uploads, social account linking.

## How to Run

### Direct Web / Mobile Browser Access:
```bash
cd TheQuest_Customer_MobileApp
python run.py
```
Open `http://localhost:5001` in your browser (or use mobile device simulation in DevTools).

### Android Deployment via Mobile Launcher:
1. Double-click `open_mobile_launcher.bat` (or run `python android_launcher.py`).
2. Click **Start Flask Server** to boot the backend on port 5001.
3. With an Android Emulator running or an authorized phone connected via USB:
   - Click **Build, Install & Launch**.
   - ADB will automatically reverse `tcp:5001 tcp:5001` and launch the app.

The launcher uses `android_studio/gradlew.bat` when available, then a Gradle installation
on `PATH` or a standard local Windows installation such as `C:\Gradle`.
It also detects the default Android SDK location and creates the ignored
`android_studio/local.properties` file automatically.
