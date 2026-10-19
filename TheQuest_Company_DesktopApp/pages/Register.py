"""
Registration Page for The Quest Hotel Management System.
Allows registering staff accounts with role assignment, contact details, and secure hashing.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import secrets
import re
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
    FONT_FAMILY, SYSTEM_NAME, SYSTEM_SUBTITLE, SYSTEM_SLOGAN
)
from utils.image_loader import get_logo_image
from utils.logger import log_auth_event

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${hashed.hex()}"

class RegisterPage(tk.Frame):
    def __init__(self, parent, show_login):
        super().__init__(parent, bg=COLOR_BG)
        self.show_login = show_login
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self, bg=COLOR_WHITE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        container.place(relx=0.5, rely=0.5, anchor="center", width=880, height=620)

        # Left Branding Panel
        left_panel = tk.Frame(container, bg=COLOR_PRIMARY, width=340)
        left_panel.pack(side="left", fill="both", expand=True)

        try:
            self.logo_img = get_logo_image((140, 140))
            tk.Label(left_panel, image=self.logo_img, bg=COLOR_PRIMARY).pack(pady=(40, 10))
        except Exception:
            tk.Label(left_panel, text="TQ", font=(FONT_FAMILY, 32, "bold"), fg=COLOR_ACCENT, bg=COLOR_PRIMARY).pack(pady=(40, 10))

        tk.Label(left_panel, text="STAFF ENROLLMENT", font=(FONT_FAMILY, 15, "bold"), fg=COLOR_WHITE, bg=COLOR_PRIMARY).pack()
        tk.Label(left_panel, text="Create Internal Account", font=(FONT_FAMILY, 10), fg=COLOR_PRIMARY_TINT, bg=COLOR_PRIMARY).pack(pady=(2, 20))

        tk.Frame(left_panel, bg=COLOR_ACCENT, height=2, width=160).pack(pady=(0, 15))

        tk.Label(
            left_panel,
            text=f'"{SYSTEM_SLOGAN}"',
            font=(FONT_FAMILY, 9, "italic"),
            fg=COLOR_ACCENT_LIGHT,
            bg=COLOR_PRIMARY,
            wraplength=260,
            justify="center"
        ).pack(padx=20)

        tk.Label(
            left_panel,
            text="Role-Based Security Policy Enforced",
            font=(FONT_FAMILY, 8),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY
        ).pack(side="bottom", pady=20)

        # Right Form Panel
        right_panel = tk.Frame(container, bg=COLOR_WHITE, padx=35, pady=25)
        right_panel.pack(side="right", fill="both", expand=True)

        tk.Label(
            right_panel,
            text="Employee Registration",
            font=(FONT_FAMILY, 18, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 2))

        tk.Label(
            right_panel,
            text="Enter employee details and operational clearance.",
            font=(FONT_FAMILY, 9),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 15))

        form = tk.Frame(right_panel, bg=COLOR_WHITE)
        form.pack(fill="x")

        self.entries = {}

        # Fields layout
        fields = [
            ("Full Name", "full_name", False),
            ("Username", "username", False),
            ("Email Address", "email", False),
            ("Mobile Phone", "phone", False),
            ("Password", "password", True),
            ("Confirm Password", "confirm_password", True)
        ]

        for i, (label_txt, f_name, is_pwd) in enumerate(fields):
            row_f = tk.Frame(form, bg=COLOR_WHITE)
            row_f.pack(fill="x", pady=2)

            tk.Label(
                row_f,
                text=label_txt,
                font=(FONT_FAMILY, 9, "bold"),
                fg=COLOR_TEXT_NORMAL,
                bg=COLOR_WHITE,
                width=15,
                anchor="w"
            ).pack(side="left")

            entry = tk.Entry(
                row_f,
                font=(FONT_FAMILY, 10),
                show="•" if is_pwd else "",
                bg=COLOR_BG,
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLOR_BORDER,
                highlightcolor=COLOR_PRIMARY
            )
            entry.pack(side="left", fill="x", expand=True, ipady=4)
            self.entries[f_name] = entry

        # Role Selector Dropdown
        role_row = tk.Frame(form, bg=COLOR_WHITE)
        role_row.pack(fill="x", pady=(6, 2))

        tk.Label(
            role_row,
            text="Assigned Role",
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_TEXT_NORMAL,
            bg=COLOR_WHITE,
            width=15,
            anchor="w"
        ).pack(side="left")

        self.role_var = tk.StringVar(value="Staff_Kitchen")
        role_combo = ttk.Combobox(
            role_row,
            textvariable=self.role_var,
            values=["Admin", "Cashier", "Staff_Kitchen", "Staff_Logistics", "Staff_Utilities"],
            state="readonly",
            font=(FONT_FAMILY, 9)
        )
        role_combo.pack(side="left", fill="x", expand=True, ipady=3)

        # Register Button
        submit_btn = tk.Button(
            right_panel,
            text="Create Employee Account",
            font=(FONT_FAMILY, 10, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground=COLOR_WHITE,
            relief="flat",
            cursor="hand2",
            command=self.register
        )
        submit_btn.pack(fill="x", ipady=7, pady=(15, 8))

        # Back to Login
        back_btn = tk.Button(
            right_panel,
            text="Already have an account? Sign in here",
            font=(FONT_FAMILY, 9),
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE,
            activebackground=COLOR_WHITE,
            activeforeground=COLOR_ACCENT,
            relief="flat",
            cursor="hand2",
            command=self.show_login
        )
        back_btn.pack()

    def register(self):
        full_name = self.entries["full_name"].get().strip()
        username = self.entries["username"].get().strip()
        email = self.entries["email"].get().strip()
        phone = self.entries["phone"].get().strip()
        password = self.entries["password"].get()
        confirm = self.entries["confirm_password"].get()
        role = self.role_var.get()

        if not all([full_name, username, email, phone, password, confirm]):
            messagebox.showwarning("Missing Information", "Please fill in all employee registration fields.")
            return

        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
            messagebox.showwarning("Invalid Username", "Username must be 3-30 letters, numbers, or underscores.")
            return

        if "@" not in email or "." not in email:
            messagebox.showwarning("Invalid Email", "Please enter a valid company or personal email address.")
            return

        if len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters.")
            return

        if password != confirm:
            messagebox.showerror("Password Mismatch", "Passwords do not match.")
            return

        pwd_hash = hash_password(password)

        try:
            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (username, password_hash, role, name, phone, email, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (username, pwd_hash, role, full_name, phone, email))
                conn.commit()

            log_auth_event(
                event_type="STAFF_REGISTERED",
                username=username,
                role=role,
                status="SUCCESS",
                details=f"New employee {full_name} enrolled with role {role}"
            )

            messagebox.showinfo(
                "Registration Successful",
                f"Account for {full_name} ({role}) has been created successfully!\nYou may now sign in."
            )
            self.show_login()

        except Exception as err:
            import sqlite3
            if isinstance(err, sqlite3.IntegrityError):
                messagebox.showerror("Registration Failed", "That username or email is already registered.")
            else:
                messagebox.showerror("Database Error", f"Could not create account: {err}")
