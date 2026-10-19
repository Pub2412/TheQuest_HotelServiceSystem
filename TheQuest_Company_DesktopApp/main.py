"""
The Quest - Hotel Management System
Main Desktop Application Entry Point
Theme: Purple, Yellow, and White
Slogan: "We shall never deny a guest, even the most ridiculous request"
"""

import tkinter as tk
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.db import initialize_database, get_connection
from utils.theme import (
    COLOR_PRIMARY_DARK, COLOR_PRIMARY, COLOR_PRIMARY_LIGHT, COLOR_PRIMARY_TINT,
    COLOR_ACCENT, COLOR_BG, COLOR_WHITE, SYSTEM_NAME, SYSTEM_SUBTITLE, SYSTEM_SLOGAN
)
try:
    from PIL import Image, ImageTk
    import fpdf
except ImportError as err:
    import tkinter.messagebox as mb
    root = tk.Tk()
    root.withdraw()
    mb.showerror(
        "Dependency Missing",
        f"A required Python package is missing: {err}\n\n"
        "Please install requirements using:\n"
        "    pip install -r requirements.txt\n"
        "or activate your project virtual environment (.venv)."
    )
    sys.exit(1)

from utils.image_loader import get_icon_logo
from utils.logger import log_system_health, log_auth_event
from pages.Login import LoginPage
from pages.Register import RegisterPage
from pages.AdminPage import AdminPage
from pages.CashierPage import CashierPage
from pages.StaffPage import StaffPage
from pages.ForbiddenPage import ForbiddenPage


class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{SYSTEM_NAME} - {SYSTEM_SUBTITLE}")
        self.geometry("1280x800")
        self.minsize(1080, 680)
        self.configure(bg=COLOR_BG)

        # Set window icon
        try:
            icon_img = get_icon_logo((32, 32))
            self.iconphoto(True, icon_img)
        except Exception:
            pass

        self.current_user = None

        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def clear_page(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_page()
        self.current_user = None
        page = LoginPage(
            self.container,
            on_login_success=self.on_login_success
        )
        page.pack(fill="both", expand=True)

    def show_register(self):
        self.clear_page()
        page = RegisterPage(
            self.container,
            show_login=self.show_login
        )
        page.pack(fill="both", expand=True)

    def on_login_success(self, user: dict):
        self.current_user = user
        role = user.get("role", "")

        # Route by role
        if role == "Admin":
            self.show_admin()
        elif role == "Cashier":
            self.show_cashier()
        elif "Staff" in role:
            self.show_staff()
        else:
            # Fallback forbidden if role unrecognized
            self.show_forbidden("Management Dashboard")

    def show_admin(self):
        self.clear_page()
        # Security check
        if not self.current_user or self.current_user.get("role") != "Admin":
            self.show_forbidden("Admin Console")
            return

        page = AdminPage(
            self.container,
            current_user=self.current_user,
            on_logout_cb=self.show_login
        )
        page.pack(fill="both", expand=True)

    def show_cashier(self):
        self.clear_page()
        # Security check
        if not self.current_user or self.current_user.get("role") != "Cashier":
            self.show_forbidden("Cashier Front Desk Portal")
            return

        page = CashierPage(
            self.container,
            current_user=self.current_user,
            on_logout_cb=self.show_login
        )
        page.pack(fill="both", expand=True)

    def show_staff(self):
        self.clear_page()
        # Security check
        user_role = self.current_user.get("role", "") if self.current_user else ""
        if "Staff" not in user_role and user_role != "Admin":
            self.show_forbidden("Staff Operations Portal")
            return

        page = StaffPage(
            self.container,
            current_user=self.current_user,
            on_logout_cb=self.show_login
        )
        page.pack(fill="both", expand=True)

    def show_forbidden(self, attempted_page: str):
        self.clear_page()
        user_info = self.current_user or {"username": "Guest", "role": "None"}
        page = ForbiddenPage(
            self.container,
            current_user=user_info,
            attempted_page=attempted_page,
            on_return_cb=self._return_to_authorized_page,
            on_logout_cb=self.show_login
        )
        page.pack(fill="both", expand=True)

    def _return_to_authorized_page(self):
        if not self.current_user:
            self.show_login()
            return
        role = self.current_user.get("role", "")
        if role == "Admin":
            self.show_admin()
        elif role == "Cashier":
            self.show_cashier()
        elif "Staff" in role:
            self.show_staff()
        else:
            self.show_login()


if __name__ == "__main__":
    # Ensure database schema is initialized and seeded if empty
    initialize_database()

    with get_connection() as conn:
        u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if u_count == 0:
            print("Users table empty, running seed_data...")
            from database.seed_data import seed_database
            seed_database()

    app = HotelApp()
    app.mainloop()
