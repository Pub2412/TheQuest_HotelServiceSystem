"""
403 Forbidden Access Page for The Quest Hotel Management System.
Displayed whenever a user attempts to access a page unauthorized for their role.
"""

import tkinter as tk
from utils.theme import (
    COLOR_PRIMARY_DARK, COLOR_PRIMARY, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_WHITE, COLOR_DANGER, COLOR_CARD, COLOR_TEXT_MUTED, FONT_FAMILY,
    SYSTEM_NAME, SYSTEM_SLOGAN
)

class ForbiddenPage(tk.Frame):
    def __init__(self, parent, current_user: dict, attempted_page: str, on_return_cb, on_logout_cb):
        super().__init__(parent, bg=COLOR_PRIMARY_DARK)
        self.current_user = current_user or {"username": "Guest", "role": "Unauthenticated"}
        self.attempted_page = attempted_page
        self.on_return_cb = on_return_cb
        self.on_logout_cb = on_logout_cb

        self._build_ui()

    def _build_ui(self):
        center_frame = tk.Frame(self, bg=COLOR_PRIMARY_DARK)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Shield Icon / Warning Badge
        tk.Label(
            center_frame,
            text="🛡️ ⛔",
            font=(FONT_FAMILY, 48),
            bg=COLOR_PRIMARY_DARK
        ).pack(pady=(0, 10))

        # Error Code
        tk.Label(
            center_frame,
            text="403",
            font=(FONT_FAMILY, 54, "bold"),
            fg=COLOR_DANGER,
            bg=COLOR_PRIMARY_DARK
        ).pack()

        # Headline
        tk.Label(
            center_frame,
            text="ACCESS FORBIDDEN",
            font=(FONT_FAMILY, 20, "bold"),
            fg=COLOR_WHITE,
            bg=COLOR_PRIMARY_DARK
        ).pack(pady=(0, 10))

        # Description Card
        card = tk.Frame(center_frame, bg=COLOR_CARD, padx=25, pady=20, highlightthickness=2, highlightbackground=COLOR_ACCENT)
        card.pack(pady=10)

        msg = (
            f"Security Clearance Violation.\n\n"
            f"You attempted to access: {self.attempted_page}\n"
            f"Logged In User: {self.current_user.get('name', self.current_user.get('username', 'User'))}\n"
            f"Assigned Role: {self.current_user.get('role', 'Unknown')}\n\n"
            f"This administrative module is strictly restricted to authorized personnel.\n"
            f"Your access attempt has been logged into the secure security audit file."
        )
        tk.Label(
            card,
            text=msg,
            font=(FONT_FAMILY, 10),
            fg="#1E293B",
            bg=COLOR_CARD,
            justify="center"
        ).pack()

        # Action Buttons
        btn_frame = tk.Frame(center_frame, bg=COLOR_PRIMARY_DARK)
        btn_frame.pack(pady=20)

        return_btn = tk.Button(
            btn_frame,
            text="← Return to My Authorized Dashboard",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_ACCENT,
            fg="#78350F",
            activebackground=COLOR_ACCENT_HOVER,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.on_return_cb
        )
        return_btn.pack(side="left", padx=10)

        logout_btn = tk.Button(
            btn_frame,
            text="Sign Out",
            font=(FONT_FAMILY, 11),
            bg="#4A1E73",
            fg=COLOR_WHITE,
            activebackground="#5E2692",
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.on_logout_cb
        )
        logout_btn.pack(side="left", padx=10)

        # Slogan Footer
        tk.Label(
            self,
            text=f"{SYSTEM_NAME}  •  \"{SYSTEM_SLOGAN}\"",
            font=(FONT_FAMILY, 9, "italic"),
            fg=COLOR_ACCENT,
            bg=COLOR_PRIMARY_DARK
        ).pack(side="bottom", pady=20)
