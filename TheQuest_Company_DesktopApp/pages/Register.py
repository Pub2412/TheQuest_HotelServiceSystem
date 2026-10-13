
import tkinter as tk
from tkinter import messagebox
import hashlib
import secrets
import hmac
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.db import get_connection


def hash_password(password):
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )
    return f"{salt.hex()}${hashed.hex()}"


class RegisterPage(tk.Frame):
    def __init__(self, parent, show_login):
        super().__init__(parent)

        self.show_login = show_login

        tk.Label(
            self,
            text="Create an Account",
            font=("Arial", 26, "bold")
        ).pack(pady=(50, 25))

        form = tk.Frame(self)
        form.pack()

        self.entries = {}

        fields = [
            ("Full Name", "full_name"),
            ("Username", "username"),
            ("Email", "email"),
            ("Password", "password"),
            ("Confirm Password", "confirm_password")
        ]

        for row, (label_text, field_name) in enumerate(fields):
            tk.Label(
                form,
                text=label_text,
                font=("Arial", 12)
            ).grid(row=row, column=0, padx=10, pady=8, sticky="e")

            entry = tk.Entry(
                form,
                font=("Arial", 12),
                width=28,
                show="*" if "password" in field_name else ""
            )
            entry.grid(row=row, column=1, padx=10, pady=8)

            self.entries[field_name] = entry

        tk.Button(
            self,
            text="Register",
            font=("Arial", 12),
            width=18,
            command=self.register
        ).pack(pady=20)

        tk.Button(
            self,
            text="Already have an account? Login",
            relief="flat",
            fg="blue",
            cursor="hand2",
            command=self.show_login
        ).pack()

    def register(self):
        full_name = self.entries["full_name"].get().strip()
        username = self.entries["username"].get().strip()
        email = self.entries["email"].get().strip()
        password = self.entries["password"].get()
        confirm = self.entries["confirm_password"].get()

        if not all([full_name, username, email, password, confirm]):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in all fields."
            )
            return

        if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
            messagebox.showwarning(
                "Invalid Username",
                "Use 3-30 letters, numbers, dots, underscores, or hyphens."
            )
            return

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            messagebox.showwarning(
                "Invalid Email",
                "Please enter a valid email address."
            )
            return

        if len(password) < 8:
            messagebox.showwarning(
                "Weak Password",
                "Your password must contain at least 8 characters."
            )
            return

        if password != confirm:
            messagebox.showerror(
                "Password Mismatch",
                "The passwords do not match."
            )
            return

        password_hash = hash_password(password)

        try:
            with get_connection() as connection:
                connection.execute("""
                    INSERT INTO users
                        (username, password_hash, name, email, role)
                    VALUES (?, ?, ?, ?, 'user')
                """, (username, password_hash, full_name, email))

        except Exception as error:
            import sqlite3

            if isinstance(error, sqlite3.IntegrityError):
                messagebox.showerror(
                    "Registration Failed",
                    "That username or email is already registered."
                )
            else:
                messagebox.showerror(
                    "Database Error",
                    "Could not create your account."
                )
            return

        messagebox.showinfo(
            "Registration Successful",
            "Your account has been created. You can now log in."
        )
        self.show_login()
