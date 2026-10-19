"""
Login Page for The Quest Hotel Management System.
Features:
- Role-based automatic redirection (Admin, Cashier, Staff)
- Security 3-strike lockout with live 60-second countdown
- Encrypted authentication logging (log_auth_event)
- Slogan and Logo presentation in Royal Purple & Gold
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
import hmac
import time
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.db import get_connection
from utils.theme import (
    COLOR_PRIMARY_DARK, COLOR_PRIMARY, COLOR_PRIMARY_LIGHT, COLOR_PRIMARY_TINT,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_ACCENT_LIGHT, COLOR_ACCENT_TEXT,
    COLOR_WHITE, COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT_DARK,
    COLOR_TEXT_NORMAL, COLOR_TEXT_MUTED, COLOR_DANGER, COLOR_SUCCESS,
    FONT_FAMILY, FONT_HEADING, FONT_SUBHEADING, FONT_TITLE, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, SYSTEM_NAME, SYSTEM_SUBTITLE, SYSTEM_SLOGAN
)
from utils.image_loader import get_logo_image
from utils.logger import log_auth_event, log_system_health

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        if not stored_hash:
            return False
        # Support PBKDF2 hash (salt$hash)
        if "$" in stored_hash:
            salt_hex, hash_hex = stored_hash.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            expected_hash = bytes.fromhex(hash_hex)
            
            # Determine iterations used (100k for fast UI seed, 600k fallback)
            for iters in [100_000, 600_000]:
                test_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
                if hmac.compare_digest(test_hash, expected_hash):
                    return True
            return False
        # Fallback direct string compare for plain test passwords
        return hmac.compare_digest(password, stored_hash)
    except Exception:
        return False

class LoginPage(tk.Frame):
    def __init__(self, parent, on_login_success, show_register=None):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.on_login_success = on_login_success
        self.show_register = show_register

        # Security lockout state
        self.failed_attempts = 0
        self.lockout_until = 0
        self.lockout_job = None

        self._build_ui()
        # Trigger system health log on page mount
        log_system_health()

    def _build_ui(self):
        # Two-column container: Left Branding Panel, Right Form Panel
        main_box = tk.Frame(self, bg=COLOR_WHITE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        main_box.place(relx=0.5, rely=0.5, anchor="center", width=860, height=540)

        # ------------------ LEFT BRANDING PANEL ------------------
        left_panel = tk.Frame(main_box, bg=COLOR_PRIMARY, width=380)
        left_panel.pack(side="left", fill="both", expand=True)

        # Logo Image
        try:
            self.logo_img = get_logo_image((160, 160))
            logo_lbl = tk.Label(left_panel, image=self.logo_img, bg=COLOR_PRIMARY)
            logo_lbl.pack(pady=(45, 10))
        except Exception:
            tk.Label(
                left_panel,
                text="TQ",
                font=(FONT_FAMILY, 36, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_PRIMARY
            ).pack(pady=(50, 10))

        tk.Label(
            left_panel,
            text=SYSTEM_NAME.upper(),
            font=(FONT_FAMILY, 20, "bold"),
            fg=COLOR_WHITE,
            bg=COLOR_PRIMARY
        ).pack()

        tk.Label(
            left_panel,
            text=SYSTEM_SUBTITLE,
            font=(FONT_FAMILY, 11),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY
        ).pack(pady=(2, 25))

        # Gold Divider
        div = tk.Frame(left_panel, bg=COLOR_ACCENT, height=2, width=180)
        div.pack(pady=(0, 20))

        # Slogan
        slogan_lbl = tk.Label(
            left_panel,
            text=f'"{SYSTEM_SLOGAN}"',
            font=(FONT_FAMILY, 10, "italic"),
            fg=COLOR_ACCENT_LIGHT,
            bg=COLOR_PRIMARY,
            wraplength=300,
            justify="center"
        )
        slogan_lbl.pack(padx=25)

        tk.Label(
            left_panel,
            text="Desktop Enterprise Portal v2.4",
            font=(FONT_FAMILY, 8),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY
        ).pack(side="bottom", pady=20)

        # ------------------ RIGHT FORM PANEL ------------------
        right_panel = tk.Frame(main_box, bg=COLOR_WHITE, padx=40, pady=30, width=480)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(
            right_panel,
            text="Employee Sign In",
            font=(FONT_FAMILY, 20, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(10, 4))

        tk.Label(
            right_panel,
            text="Please authenticate with your staff credentials.",
            font=(FONT_FAMILY, 10),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 20))

        # Lockout Alert Banner
        self.lockout_banner = tk.Label(
            right_panel,
            text="",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_DANGER,
            fg=COLOR_WHITE,
            padx=10,
            pady=6
        )

        # Form Fields
        form = tk.Frame(right_panel, bg=COLOR_WHITE)
        form.pack(fill="x")

        # Username
        tk.Label(
            form,
            text="Username or Staff ID",
            font=(FONT_FAMILY, 10, "bold"),
            fg=COLOR_TEXT_NORMAL,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(5, 3))

        self.username_entry = tk.Entry(
            form,
            font=(FONT_FAMILY, 11),
            bg=COLOR_BG,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_PRIMARY
        )
        self.username_entry.pack(fill="x", ipady=7, pady=(0, 12))

        # Password
        tk.Label(
            form,
            text="Password",
            font=(FONT_FAMILY, 10, "bold"),
            fg=COLOR_TEXT_NORMAL,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(5, 3))

        self.password_entry = tk.Entry(
            form,
            font=(FONT_FAMILY, 11),
            show="•",
            bg=COLOR_BG,
            relief="flat",
            highlightthickness=1,
            highlightbackground=COLOR_BORDER,
            highlightcolor=COLOR_PRIMARY
        )
        self.password_entry.pack(fill="x", ipady=7, pady=(0, 15))
        self.password_entry.bind("<Return>", lambda e: self.login())
        self.username_entry.bind("<Return>", lambda e: self.login())

        # Sign In Button
        self.login_btn = tk.Button(
            right_panel,
            text="Sign In to System",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground=COLOR_WHITE,
            relief="flat",
            cursor="hand2",
            command=self.login
        )
        self.login_btn.pack(fill="x", ipady=8, pady=(10, 15))

        # Security notice (Registration handled solely by Administrator)
        tk.Label(
            right_panel,
            text="🔒 Staff accounts are provisioned exclusively by System Administrators.",
            font=(FONT_FAMILY, 8, "italic"),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_WHITE,
            wraplength=340,
            justify="center"
        ).pack(pady=(0, 10))

        # Demo Credentials Helper Hint
        hint_frame = tk.Frame(right_panel, bg=COLOR_ACCENT_LIGHT, padx=10, pady=8)
        hint_frame.pack(fill="x", side="bottom")

        tk.Label(
            hint_frame,
            text="Demo Shortcuts: admin / admin123  •  cashier / cashier123\nkitchen / kitchen123  •  logistics / logistics123  •  utilities / utilities123",
            font=(FONT_FAMILY, 8),
            fg=COLOR_ACCENT_TEXT,
            bg=COLOR_ACCENT_LIGHT,
            justify="center"
        ).pack()

    def login(self):
        # Check lockout
        now = time.time()
        if now < self.lockout_until:
            remaining = int(self.lockout_until - now)
            messagebox.showwarning(
                "System Locked",
                f"Too many failed login attempts.\nPlease wait {remaining} second(s) before trying again."
            )
            return

        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Credentials",
                "Please enter both your username and password."
            )
            return

        try:
            with get_connection() as conn:
                account = conn.execute("""
                    SELECT id, username, password_hash, name, role, is_active, phone, image_path, email
                    FROM users
                    WHERE username = ?
                """, (username,)).fetchone()

            if account and account["is_active"] and verify_password(password, account["password_hash"]):
                # Success
                self.failed_attempts = 0
                log_auth_event(
                    event_type="LOGIN_SUCCESS",
                    username=username,
                    role=account["role"],
                    status="SUCCESS",
                    details=f"User {account['name']} logged in successfully"
                )

                # Convert row to dictionary
                user_data = dict(account)
                self.on_login_success(user_data)
            else:
                self._handle_failed_login(username)

        except Exception as err:
            messagebox.showerror(
                "Database Connection Error",
                f"Could not connect to hotel database:\n{err}"
            )

    def _handle_failed_login(self, username: str):
        self.failed_attempts += 1
        log_auth_event(
            event_type="LOGIN_FAILED",
            username=username,
            role="Unknown",
            status="FAILURE",
            details=f"Failed password attempt ({self.failed_attempts}/3)"
        )

        if self.failed_attempts >= 3:
            # 1-minute lockout (60 seconds)
            self.lockout_until = time.time() + 60
            self.failed_attempts = 0
            log_auth_event(
                event_type="ACCOUNT_LOCKOUT",
                username=username,
                role="Unknown",
                status="LOCKOUT",
                details="User locked out for 60 seconds after 3 failed tries."
            )
            self._start_lockout_countdown()
        else:
            remaining = 3 - self.failed_attempts
            messagebox.showerror(
                "Authentication Failed",
                f"Invalid username or password.\nYou have {remaining} attempt(s) remaining before a 1-minute lockout."
            )

    def _start_lockout_countdown(self):
        self.login_btn.config(state="disabled", bg=COLOR_BORDER)
        self.username_entry.config(state="disabled")
        self.password_entry.config(state="disabled")
        self.lockout_banner.pack(fill="x", pady=(0, 10), before=self.login_btn)
        self._update_countdown()

    def _update_countdown(self):
        now = time.time()
        remaining = int(self.lockout_until - now)
        if remaining > 0:
            self.lockout_banner.config(
                text=f"⚠️ System locked due to 3 failed attempts. Try again in {remaining}s."
            )
            self.lockout_job = self.after(1000, self._update_countdown)
        else:
            self.lockout_banner.pack_forget()
            self.login_btn.config(state="normal", bg=COLOR_PRIMARY)
            self.username_entry.config(state="normal")
            self.password_entry.config(state="normal")
            messagebox.showinfo("Lockout Expired", "You may now attempt to sign in again.")
