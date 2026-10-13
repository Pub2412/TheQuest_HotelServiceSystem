
import tkinter as tk
from tkinter import messagebox
import hashlib
import hmac
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.db import get_connection


def verify_password(password, stored_hash):
    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000
        )

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False


class LoginPage(tk.Frame):
    def __init__(self, parent, show_register):
        super().__init__(parent)

        self.show_register = show_register

        tk.Label(
            self,
            text="The Quest Company",
            font=("Arial", 28, "bold")
        ).pack(pady=(100, 10))

        tk.Label(
            self,
            text="Hotel Management System",
            font=("Arial", 17)
        ).pack(pady=(0, 30))

        form = tk.Frame(self)
        form.pack()

        tk.Label(
            form, text="Username:", font=("Arial", 12)
        ).grid(row=0, column=0, padx=10, pady=10, sticky="e")

        self.username_entry = tk.Entry(
            form, font=("Arial", 12), width=28
        )
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(
            form, text="Password:", font=("Arial", 12)
        ).grid(row=1, column=0, padx=10, pady=10, sticky="e")

        self.password_entry = tk.Entry(
            form, font=("Arial", 12), width=28, show="*"
        )
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Button(
            self,
            text="Login",
            font=("Arial", 12),
            width=18,
            command=self.login
        ).pack(pady=20)

        tk.Button(
            self,
            text="Don't have an account? Register",
            relief="flat",
            fg="blue",
            cursor="hand2",
            command=self.show_register
        ).pack()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Enter your username and password."
            )
            return

        with get_connection() as connection:
            account = connection.execute("""
                SELECT id AS user_id, username, password_hash,
                       name AS full_name, role
                FROM users
                WHERE username = ? AND is_active = 1
            """, (username,)).fetchone()

        if account and verify_password(password, account["password_hash"]):
            messagebox.showinfo(
                "Login Successful",
                f"Welcome, {account['full_name']}!\n"
                f"Role: {account['role'].title()}"
            )

            # Later, navigate to the dashboard for this role.
            # Example: self.controller.show_page(...)

        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password."
            )
