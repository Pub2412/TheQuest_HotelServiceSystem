# The Quest Hotel Service System

The Quest is a Python-based hotel management system with shared SQLite data and
three client applications:

- **Company Desktop App** - staff administration, reservations, inventory,
  messaging, and hotel operations.
- **Company Mobile App** - a Flask/WebView Android client for staff workflows.
- **Customer Website and Mobile App** - guest reservations, stays, services,
  loyalty rewards, messaging, and digital room access.

The project also includes a smart-lock simulator in `gui.py` for testing room
key access and door state synchronization.

## Authors

- Pub - Lance Grant E. Haboc
- stix - John Sherwin E. Padilla

## Project structure

```text
assets/                         Shared logos, room images, and service assets
database/                       Shared SQLite database and data services
documentation/                  Development history and project notes
TheQuest_Company_DesktopApp/   Tkinter desktop application
TheQuest_Company_MobileApp/    Staff Flask app and Android WebView project
TheQuest_Customer_MobileApp/   Guest Flask app and Android WebView project
TheQuest_Customer_Website/     Guest Flask website
gui.py                         Smart-lock simulator
```

## Requirements

- Windows, macOS, or Linux for the Python applications
- Python 3.8 or newer
- Python packages listed in each application's `requirements.txt`
- Android SDK, Platform-Tools, and Gradle for Android builds
- An Android emulator or USB-debugged Android device for mobile deployment

The applications use the shared database at:

```text
database/hotel_service.db
```

Do not commit credentials, private keys, or production database copies.

## Running the applications

Run commands from the repository root unless stated otherwise.

### Company Desktop App

Install its dependencies and start the Tkinter application:

```powershell
cd TheQuest_Company_DesktopApp
python -m pip install -r requirements.txt
python main.py
```

The desktop application uses the shared Quest branding. Its title bar and
taskbar identity use `assets/imgs/logo/logo.ico`, which has a purple
background and the Quest logo mark.

### Smart-lock simulator

```powershell
python gui.py
```

The simulator reads the shared database and displays room lock state, access
events, regular room keys, and the daily staff super key.

### Company Mobile App

Start the staff Flask server:

```powershell
cd TheQuest_Company_MobileApp
python -m pip install -r requirements.txt
python run.py
```

For Android deployment, run `open_mobile_launcher.bat`. The launcher can start
the Flask server, build the WebView APK, install it, and launch it on an
authorized emulator or USB device.

### Customer Mobile App

```powershell
cd TheQuest_Customer_MobileApp
python -m pip install -r requirements.txt
python run.py
```

For Android deployment, run `open_mobile_launcher.bat`. The customer mobile
server uses port `5001`; the Android WebView uses the emulator address
`10.0.2.2:5001` or a USB reverse-ADB connection.

### Customer Website

```powershell
cd TheQuest_Customer_Website
python -m pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000` in a browser. On Windows, `run.bat` can be used
as the one-click launcher.

## Branding

The shared logo assets are stored in `assets/imgs/logo/`:

- `logo.png` - compact logo mark used for app icons and navigation branding.
- `logotitle.png` - full logo/title artwork used in login and splash screens.
- `logo.ico` - purple-backed Windows icon for the desktop application.

## Development notes

- Flask clients run locally and share the repository SQLite database.
- Android clients are WebView shells around their corresponding Flask app.
- Authentication and room-access behavior should be tested against the shared
  database after schema or reservation changes.
- Keep generated build folders, virtual environments, caches, and local
  Android SDK configuration out of commits.

See [`documentation/dev-logs.txt`](documentation/dev-logs.txt) for the project
change history and [`HOW_TO_RUN.md`](TheQuest_Customer_MobileApp/HOW_TO_RUN.md)
for the customer mobile deployment guide.
