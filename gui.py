"""
The Quest Hotel - Smart Lock Hardware Simulator & Door Access Testbed GUI.
Theme: Royal Purple (#23073D, #3B185F), Warm Gold (#F59E0B), Clean Ivory White.

Features:
1. Daily Super Key (rotated daily, stored hashed in DB, used by staff).
2. Regular Room Keys (minted on check-in, hashed in DB, revoked on checkout).
3. Test Wi-Fi Proximity Door Access (requires connection to room's matching Wi-Fi).
4. Test NFC Tap Proximity Door Access (physical proximity tap, checks key hash).
5. Visual Door Lock Display (Locked [Red] vs Unlocked [Green], physical door state, auto-relock timer).
6. Real-time background sync with hotel_service.db so actions from Customer & Company Mobile Apps
   are visually displayed here live!
"""

import os
import sys
import time
from datetime import datetime, date
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Resolve project paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.key_service import (
    init_key_system, get_daily_super_key, rotate_daily_super_key,
    verify_door_access, set_door_state, get_all_rooms_door_status,
    get_door_access_logs, get_room_key_by_room_id, mint_room_key,
    revoke_room_key, hash_key, STAFF_WIFI_SSID
)

# Color Palette
COLOR_PRIMARY_DARK = "#23073D"
COLOR_PRIMARY = "#3B185F"
COLOR_PRIMARY_LIGHT = "#581C87"
COLOR_PRIMARY_TINT = "#EDE9FE"
COLOR_ACCENT = "#F59E0B"
COLOR_ACCENT_LIGHT = "#FEF3C7"
COLOR_ACCENT_TEXT = "#78350F"
COLOR_BG = "#F8FAFC"
COLOR_CARD = "#FFFFFF"
COLOR_BORDER = "#E2E8F0"
COLOR_TEXT_DARK = "#0F172A"
COLOR_TEXT_MUTED = "#64748B"
COLOR_SUCCESS = "#10B981"
COLOR_SUCCESS_BG = "#ECFDF5"
COLOR_SUCCESS_TEXT = "#065F46"
COLOR_DANGER = "#EF4444"
COLOR_DANGER_BG = "#FEF2F2"
COLOR_DANGER_TEXT = "#991B1B"
FONT_FAMILY = "Segoe UI"


class DoorSimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The Quest Hotel - Smart Lock Simulator & Door Access Testbed")
        self.geometry("1100x780")
        self.minsize(980, 680)
        self.configure(bg=COLOR_BG)

        # Initialize schema & keys
        init_key_system()

        self.rooms_data = []
        self.selected_room = None
        self.auto_relock_after_id = None
        self.relock_countdown = 0

        self._init_styles()
        self._build_ui()
        self.refresh_all_data()

        # Start live background polling (polls DB every 1.5s for live cross-app sync)
        self.after(1500, self._poll_background_status)

    def _init_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Card.TFrame", background=COLOR_CARD, relief="flat")
        style.configure("TLabel", background=COLOR_BG, font=(FONT_FAMILY, 10), foreground=COLOR_TEXT_DARK)
        style.configure("Header.TLabel", font=(FONT_FAMILY, 15, "bold"), foreground=COLOR_PRIMARY_DARK)
        style.configure("Subheader.TLabel", font=(FONT_FAMILY, 11, "bold"), foreground=COLOR_PRIMARY)
        style.configure("Muted.TLabel", font=(FONT_FAMILY, 9), foreground=COLOR_TEXT_MUTED)

        style.configure("Treeview", font=(FONT_FAMILY, 9), rowheight=24)
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 9, "bold"), background=COLOR_PRIMARY_TINT, foreground=COLOR_PRIMARY_DARK)

    def _build_ui(self):
        # 1. Top Header Bar
        top_bar = tk.Frame(self, bg=COLOR_PRIMARY_DARK, height=65)
        top_bar.pack(fill="x", side="top")

        title_frame = tk.Frame(top_bar, bg=COLOR_PRIMARY_DARK)
        title_frame.pack(side="left", padx=20, pady=10)

        tk.Label(
            title_frame, text="THE QUEST HOTEL • SMART LOCK SIMULATOR",
            font=(FONT_FAMILY, 14, "bold"), fg="#FFFFFF", bg=COLOR_PRIMARY_DARK
        ).pack(anchor="w")

        tk.Label(
            title_frame, text="Super Key (Staff Daily) + Regular Keys (Hashed in DB) + Wi-Fi & NFC Testbed",
            font=(FONT_FAMILY, 9), fg=COLOR_ACCENT, bg=COLOR_PRIMARY_DARK
        ).pack(anchor="w")

        # Top Right Controls
        ctrl_frame = tk.Frame(top_bar, bg=COLOR_PRIMARY_DARK)
        ctrl_frame.pack(side="right", padx=20, pady=14)

        tk.Button(
            ctrl_frame, text="🔄 Refresh All", command=self.refresh_all_data,
            font=(FONT_FAMILY, 9, "bold"), bg=COLOR_ACCENT, fg="#FFFFFF",
            relief="flat", padx=12, pady=4, cursor="hand2"
        ).pack(side="right")

        # 2. Main Scrollable Container or Split Pane
        main_split = tk.PanedWindow(self, orient="horizontal", bg=COLOR_BORDER, sashwidth=4)
        main_split.pack(fill="both", expand=True, padx=14, pady=10)

        # Left Panel: Lock Visualization & Interactive Actions
        left_pane = tk.Frame(main_split, bg=COLOR_BG)
        main_split.add(left_pane, minsize=480, width=540)

        # Right Panel: Rooms Overview Grid & Live Event Logs
        right_pane = tk.Frame(main_split, bg=COLOR_BG)
        main_split.add(right_pane, minsize=420)

        self._build_left_pane(left_pane)
        self._build_right_pane(right_pane)

    def _build_left_pane(self, parent):
        canvas = tk.Canvas(parent, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=COLOR_BG)

        scroll_content.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- A. Daily Super Key Status Card ---
        sk_card = tk.LabelFrame(
            scroll_content, text=" 👑 TODAY'S DAILY STAFF SUPER KEY (HASHED IN DB) ",
            font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY_DARK, bg=COLOR_CARD,
            padx=14, pady=10, relief="solid", bd=1
        )
        sk_card.pack(fill="x", pady=(0, 10), padx=4)

        sk_row1 = tk.Frame(sk_card, bg=COLOR_CARD)
        sk_row1.pack(fill="x", pady=2)
        tk.Label(sk_row1, text="Date:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_CARD).pack(side="left")
        self.lbl_sk_date = tk.Label(sk_row1, text="", font=(FONT_FAMILY, 9), bg=COLOR_CARD)
        self.lbl_sk_date.pack(side="left", padx=6)

        self.btn_rotate_sk = tk.Button(
            sk_row1, text="Rotate Super Key (Simulate Day Change)",
            font=(FONT_FAMILY, 8, "bold"), bg=COLOR_ACCENT_LIGHT, fg=COLOR_ACCENT_TEXT,
            relief="groove", padx=8, pady=2, cursor="hand2", command=self._rotate_super_key
        )
        self.btn_rotate_sk.pack(side="right")

        sk_row2 = tk.Frame(sk_card, bg=COLOR_CARD)
        sk_row2.pack(fill="x", pady=4)
        tk.Label(sk_row2, text="Plain Key:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_CARD).pack(side="left")
        self.lbl_sk_plain = tk.Label(
            sk_row2, text="", font=("Courier New", 11, "bold"),
            bg="#FEF3C7", fg="#78350F", padx=6, pady=2
        )
        self.lbl_sk_plain.pack(side="left", padx=6)

        sk_row3 = tk.Frame(sk_card, bg=COLOR_CARD)
        sk_row3.pack(fill="x", pady=2)
        tk.Label(sk_row3, text="DB SHA-256 Hash:", font=(FONT_FAMILY, 8, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(side="left")
        self.lbl_sk_hash = tk.Label(sk_row3, text="", font=("Courier New", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
        self.lbl_sk_hash.pack(side="left", padx=6)

        # --- B. Room Selection & Hardware State Display ---
        room_card = tk.LabelFrame(
            scroll_content, text=" 🚪 SELECTED ROOM HARDWARE DISPLAY ",
            font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY_DARK, bg=COLOR_CARD,
            padx=14, pady=10, relief="solid", bd=1
        )
        room_card.pack(fill="x", pady=(0, 10), padx=4)

        sel_row = tk.Frame(room_card, bg=COLOR_CARD)
        sel_row.pack(fill="x", pady=4)
        tk.Label(sel_row, text="Select Room to Test:", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_CARD).pack(side="left")

        self.room_combo_var = tk.StringVar()
        self.room_combo = ttk.Combobox(sel_row, textvariable=self.room_combo_var, state="readonly", width=34)
        self.room_combo.pack(side="left", padx=10)
        self.room_combo.bind("<<ComboboxSelected>>", self._on_room_selected)

        # Visual Lock Box (Big graphic indicator)
        self.lock_display_box = tk.Frame(room_card, bg=COLOR_DANGER_BG, relief="solid", bd=2, padx=16, pady=14)
        self.lock_display_box.pack(fill="x", pady=10)

        self.lbl_lock_icon = tk.Label(self.lock_display_box, text="🔒", font=(FONT_FAMILY, 40), bg=COLOR_DANGER_BG, fg=COLOR_DANGER_TEXT)
        self.lbl_lock_icon.pack()

        self.lbl_lock_status = tk.Label(
            self.lock_display_box, text="DOOR LOCKED",
            font=(FONT_FAMILY, 16, "bold"), bg=COLOR_DANGER_BG, fg=COLOR_DANGER_TEXT
        )
        self.lbl_lock_status.pack()

        self.lbl_door_position = tk.Label(
            self.lock_display_box, text="Physical Door: CLOSED",
            font=(FONT_FAMILY, 10, "bold"), bg=COLOR_DANGER_BG, fg=COLOR_TEXT_DARK
        )
        self.lbl_door_position.pack(pady=2)

        self.lbl_timer_notice = tk.Label(
            self.lock_display_box, text="", font=(FONT_FAMILY, 9, "italic"),
            bg=COLOR_DANGER_BG, fg=COLOR_DANGER_TEXT
        )
        self.lbl_timer_notice.pack()

        # Room Metadata Specs
        meta_frame = tk.Frame(room_card, bg=COLOR_CARD)
        meta_frame.pack(fill="x", pady=4)

        self.lbl_room_guest = tk.Label(meta_frame, text="Occupant: None (Vacant)", font=(FONT_FAMILY, 9), bg=COLOR_CARD)
        self.lbl_room_guest.pack(anchor="w")

        self.lbl_room_wifi = tk.Label(meta_frame, text="Room Designated Wi-Fi: Quest_Room_101", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY)
        self.lbl_room_wifi.pack(anchor="w")

        self.lbl_room_key = tk.Label(meta_frame, text="Active Regular Key: None", font=(FONT_FAMILY, 9), bg=COLOR_CARD)
        self.lbl_room_key.pack(anchor="w")

        self.lbl_room_key_hash = tk.Label(meta_frame, text="Active Key Hash: None", font=("Courier New", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED)
        self.lbl_room_key_hash.pack(anchor="w")

        # --- C. Test Actions Panel ---
        act_card = tk.LabelFrame(
            scroll_content, text=" 🧪 DOOR ACCESS TESTING CONTROLS ",
            font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY_DARK, bg=COLOR_CARD,
            padx=14, pady=10, relief="solid", bd=1
        )
        act_card.pack(fill="x", pady=(0, 10), padx=4)

        # 1. WiFi Test Section
        tk.Label(act_card, text="1. Test Access via Wi-Fi Proximity:", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", pady=(2, 2))
        tk.Label(act_card, text="Rule: Customer & Staff must be connected to room's matching Wi-Fi (Staff can also use Staff Wi-Fi).", font=(FONT_FAMILY, 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")

        wifi_row = tk.Frame(act_card, bg=COLOR_CARD)
        wifi_row.pack(fill="x", pady=4)

        tk.Label(wifi_row, text="Simulated Wi-Fi:", font=(FONT_FAMILY, 9), bg=COLOR_CARD).pack(side="left")
        self.wifi_test_var = tk.StringVar(value="MATCHING")
        self.combo_wifi_test = ttk.Combobox(
            wifi_row, textvariable=self.wifi_test_var, state="readonly", width=28,
            values=[
                "Matching Room Wi-Fi",
                "Quest_Staff_Secure (Staff Master Wi-Fi)",
                "Quest_Lobby_Guest_WiFi (Mismatched)",
                "Cellular_5G (No Wi-Fi Connection)"
            ]
        )
        self.combo_wifi_test.pack(side="left", padx=8)

        btn_wifi_row = tk.Frame(act_card, bg=COLOR_CARD)
        btn_wifi_row.pack(fill="x", pady=4)

        tk.Button(
            btn_wifi_row, text="📶 Test Guest Wi-Fi Unlock",
            font=(FONT_FAMILY, 9, "bold"), bg="#3B82F6", fg="#FFFFFF",
            relief="flat", padx=10, pady=4, cursor="hand2", command=lambda: self._test_unlock(method="wifi", user_type="customer")
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_wifi_row, text="📶 Test Staff Super Key Wi-Fi",
            font=(FONT_FAMILY, 9, "bold"), bg=COLOR_PRIMARY, fg="#FFFFFF",
            relief="flat", padx=10, pady=4, cursor="hand2", command=lambda: self._test_unlock(method="wifi", user_type="staff")
        ).pack(side="left")

        ttk.Separator(act_card, orient="horizontal").pack(fill="x", pady=10)

        # 2. NFC Test Section
        tk.Label(act_card, text="2. Test Access via NFC Tap Proximity:", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", pady=(2, 2))
        tk.Label(act_card, text="Rule: Physical proximity verified by NFC tap. Wi-Fi restriction bypassed.", font=(FONT_FAMILY, 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(anchor="w")

        btn_nfc_row = tk.Frame(act_card, bg=COLOR_CARD)
        btn_nfc_row.pack(fill="x", pady=4)

        tk.Button(
            btn_nfc_row, text="📡 Simulate Guest NFC Tap",
            font=(FONT_FAMILY, 9, "bold"), bg="#8B5CF6", fg="#FFFFFF",
            relief="flat", padx=10, pady=4, cursor="hand2", command=lambda: self._test_unlock(method="nfc", user_type="customer")
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_nfc_row, text="📡 Simulate Staff Master NFC Tap",
            font=(FONT_FAMILY, 9, "bold"), bg=COLOR_ACCENT, fg="#FFFFFF",
            relief="flat", padx=10, pady=4, cursor="hand2", command=lambda: self._test_unlock(method="nfc", user_type="staff")
        ).pack(side="left")

        ttk.Separator(act_card, orient="horizontal").pack(fill="x", pady=10)

        # 3. Security Failure Tests & Manual Hardware Override
        tk.Label(act_card, text="3. Security Attack Tests & Manual Controls:", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_CARD, fg=COLOR_PRIMARY).pack(anchor="w", pady=(2, 2))

        btn_sec_row = tk.Frame(act_card, bg=COLOR_CARD)
        btn_sec_row.pack(fill="x", pady=4)

        tk.Button(
            btn_sec_row, text="⚠️ Test Invalid / Fake Key",
            font=(FONT_FAMILY, 8, "bold"), bg="#F1F5F9", fg=COLOR_DANGER_TEXT,
            relief="groove", padx=8, pady=3, cursor="hand2", command=self._test_fake_key
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_sec_row, text="⚠️ Test Revoked / Expired Key",
            font=(FONT_FAMILY, 8, "bold"), bg="#F1F5F9", fg=COLOR_DANGER_TEXT,
            relief="groove", padx=8, pady=3, cursor="hand2", command=self._test_revoked_key
        ).pack(side="left")

        # Hardware manual toggle buttons
        btn_override_row = tk.Frame(act_card, bg=COLOR_CARD)
        btn_override_row.pack(fill="x", pady=6)

        tk.Button(
            btn_override_row, text="🔓 Force Unlock",
            font=(FONT_FAMILY, 8, "bold"), bg=COLOR_SUCCESS_BG, fg=COLOR_SUCCESS_TEXT,
            relief="groove", padx=8, pady=3, cursor="hand2", command=lambda: self._manual_door_state("unlocked")
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            btn_override_row, text="🔒 Force Lock",
            font=(FONT_FAMILY, 8, "bold"), bg=COLOR_DANGER_BG, fg=COLOR_DANGER_TEXT,
            relief="groove", padx=8, pady=3, cursor="hand2", command=lambda: self._manual_door_state("locked")
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            btn_override_row, text="🚪 Open Physical Door",
            font=(FONT_FAMILY, 8), bg="#FFFFFF", fg=COLOR_TEXT_DARK,
            relief="groove", padx=8, pady=3, cursor="hand2", command=lambda: self._set_physical_door("OPEN")
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            btn_override_row, text="🚪 Close Physical Door",
            font=(FONT_FAMILY, 8), bg="#FFFFFF", fg=COLOR_TEXT_DARK,
            relief="groove", padx=8, pady=3, cursor="hand2", command=lambda: self._set_physical_door("CLOSED")
        ).pack(side="left")

        # Checkin/checkout simulation buttons
        btn_life_row = tk.Frame(act_card, bg=COLOR_CARD)
        btn_life_row.pack(fill="x", pady=(4, 0))

        tk.Button(
            btn_life_row, text="🏷️ Mint New Regular Key (Check-In)",
            font=(FONT_FAMILY, 8), bg=COLOR_PRIMARY_TINT, fg=COLOR_PRIMARY,
            relief="groove", padx=8, pady=3, cursor="hand2", command=self._simulate_checkin_mint
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btn_life_row, text="🏷️ Revoke Regular Key (Check-Out)",
            font=(FONT_FAMILY, 8), bg=COLOR_DANGER_BG, fg=COLOR_DANGER_TEXT,
            relief="groove", padx=8, pady=3, cursor="hand2", command=self._simulate_checkout_revoke
        ).pack(side="left")

    def _build_right_pane(self, parent):
        # Top half: Rooms Table
        rooms_box = tk.LabelFrame(
            parent, text=" 🏨 ALL ROOMS DOOR & KEY MONITOR ",
            font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY_DARK, bg=COLOR_CARD,
            padx=10, pady=10, relief="solid", bd=1
        )
        rooms_box.pack(fill="both", expand=True, pady=(0, 8), padx=4)

        room_cols = ("room", "type", "occupant", "wifi", "door", "active_key")
        self.tree_rooms = ttk.Treeview(rooms_box, columns=room_cols, show="headings", height=8)

        self.tree_rooms.heading("room", text="Room")
        self.tree_rooms.heading("type", text="Suite Type")
        self.tree_rooms.heading("occupant", text="Guest / Status")
        self.tree_rooms.heading("wifi", text="Wi-Fi SSID")
        self.tree_rooms.heading("door", text="Door State")
        self.tree_rooms.heading("active_key", text="Regular Key")

        self.tree_rooms.column("room", width=60, anchor="center")
        self.tree_rooms.column("type", width=120)
        self.tree_rooms.column("occupant", width=120)
        self.tree_rooms.column("wifi", width=110)
        self.tree_rooms.column("door", width=75, anchor="center")
        self.tree_rooms.column("active_key", width=130)

        tree_scroll_y = ttk.Scrollbar(rooms_box, orient="vertical", command=self.tree_rooms.yview)
        self.tree_rooms.configure(yscrollcommand=tree_scroll_y.set)

        self.tree_rooms.pack(side="left", fill="both", expand=True)
        tree_scroll_y.pack(side="right", fill="y")

        self.tree_rooms.bind("<<TreeviewSelect>>", self._on_tree_room_selected)

        # Bottom half: Door Access Audit Log Table
        logs_box = tk.LabelFrame(
            parent, text=" 📜 REAL-TIME ACCESS AUDIT LOGS ",
            font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY_DARK, bg=COLOR_CARD,
            padx=10, pady=10, relief="solid", bd=1
        )
        logs_box.pack(fill="both", expand=True, padx=4)

        log_cols = ("time", "room", "method", "key_type", "actor", "status", "reason")
        self.tree_logs = ttk.Treeview(logs_box, columns=log_cols, show="headings", height=8)

        self.tree_logs.heading("time", text="Timestamp")
        self.tree_logs.heading("room", text="Room")
        self.tree_logs.heading("method", text="Method")
        self.tree_logs.heading("key_type", text="Key Type")
        self.tree_logs.heading("actor", text="Actor")
        self.tree_logs.heading("status", text="Result")
        self.tree_logs.heading("reason", text="Reason / Details")

        self.tree_logs.column("time", width=110)
        self.tree_logs.column("room", width=55, anchor="center")
        self.tree_logs.column("method", width=65, anchor="center")
        self.tree_logs.column("key_type", width=80)
        self.tree_logs.column("actor", width=95)
        self.tree_logs.column("status", width=70, anchor="center")
        self.tree_logs.column("reason", width=180)

        log_scroll_y = ttk.Scrollbar(logs_box, orient="vertical", command=self.tree_logs.yview)
        self.tree_logs.configure(yscrollcommand=log_scroll_y.set)

        self.tree_logs.pack(side="left", fill="both", expand=True)
        log_scroll_y.pack(side="right", fill="y")

        # Color tags
        self.tree_rooms.tag_configure("unlocked", background="#DCFCE7")
        self.tree_rooms.tag_configure("locked", background="#FFFFFF")

        self.tree_logs.tag_configure("granted", background="#DCFCE7", foreground="#166534")
        self.tree_logs.tag_configure("denied", background="#FEE2E2", foreground="#991B1B")

    # --- Data & UI Refresh Methods ---
    def refresh_all_data(self):
        # 1. Update Daily Super Key display
        sk = get_daily_super_key()
        self.lbl_sk_date.config(text=sk["key_date"])
        self.lbl_sk_plain.config(text=sk["plain_key"])
        self.lbl_sk_hash.config(text=sk["key_hash"])

        # 2. Update Rooms Data
        self.rooms_data = get_all_rooms_door_status()
        combo_vals = []
        for r in self.rooms_data:
            occ = f"({r['guest_name']})" if r["guest_name"] else f"({r['status']})"
            combo_vals.append(f"Room {r['room_number']} - {r['type']} {occ}")

        self.room_combo["values"] = combo_vals

        # Keep current selection or default to first
        cur_idx = 0
        if self.selected_room:
            for idx, r in enumerate(self.rooms_data):
                if r["id"] == self.selected_room["id"]:
                    cur_idx = idx
                    break
        if combo_vals:
            self.room_combo.current(cur_idx)
            self._select_room_by_index(cur_idx)

        # 3. Populate Rooms Table
        self.tree_rooms.delete(*self.tree_rooms.get_children())
        for r in self.rooms_data:
            tag = "unlocked" if r["door_state"] == "unlocked" else "locked"
            occupant_str = r["guest_name"] if r["guest_name"] else r["status"]
            key_str = r["active_key"] if r["active_key"] else "None (Vacant)"
            self.tree_rooms.insert(
                "", "end", iid=str(r["id"]),
                values=(
                    r["room_number"], r["type"], occupant_str,
                    r["wifi_ssid"], r["door_state"].upper(), key_str
                ),
                tags=(tag,)
            )

        # 4. Populate Logs
        self._refresh_logs()

    def _refresh_logs(self):
        logs = get_door_access_logs(limit=40)
        self.tree_logs.delete(*self.tree_logs.get_children())
        for log in logs:
            tag = log["status"].lower()
            self.tree_logs.insert(
                "", "end",
                values=(
                    log["timestamp"], f"R{log['room_number']}", log["method"].upper(),
                    log["key_type"], log["user_name"] or log["user_type"],
                    log["status"].upper(), log["reason"]
                ),
                tags=(tag,)
            )

    def _poll_background_status(self):
        """Polls database quietly to reflect changes made from mobile apps or other processes."""
        try:
            rooms = get_all_rooms_door_status()
            if self.selected_room:
                # Find current selected room in new data
                for r in rooms:
                    if r["id"] == self.selected_room["id"]:
                        if r["door_state"] != self.selected_room["door_state"]:
                            self.selected_room = r
                            self._update_lock_display(r["door_state"])
                        break
            # Update logs count or tree items
            self._refresh_logs()
        except Exception:
            pass
        finally:
            self.after(1500, self._poll_background_status)

    def _select_room_by_index(self, idx):
        if 0 <= idx < len(self.rooms_data):
            self.selected_room = self.rooms_data[idx]
            r = self.selected_room

            # Update Metadata labels
            occ_text = f"Occupant: {r['guest_name']} ({r['status']})" if r["guest_name"] else f"Occupant: None ({r['status']})"
            self.lbl_room_guest.config(text=occ_text)
            self.lbl_room_wifi.config(text=f"Room Designated Wi-Fi: {r['wifi_ssid']}")
            self.lbl_room_key.config(text=f"Active Regular Key: {r['active_key'] or 'None (Minted on Check-In)'}")
            self.lbl_room_key_hash.config(text=f"Active Key Hash: {r['active_key_hash'] or 'None'}")

            # Update Lock Display
            self._update_lock_display(r["door_state"])

    def _on_room_selected(self, event=None):
        idx = self.room_combo.current()
        self._select_room_by_index(idx)

    def _on_tree_room_selected(self, event=None):
        sel = self.tree_rooms.selection()
        if sel:
            room_id = int(sel[0])
            for idx, r in enumerate(self.rooms_data):
                if r["id"] == room_id:
                    self.room_combo.current(idx)
                    self._select_room_by_index(idx)
                    break

    def _update_lock_display(self, state):
        is_unlocked = (state == "unlocked")
        bg_col = COLOR_SUCCESS_BG if is_unlocked else COLOR_DANGER_BG
        text_col = COLOR_SUCCESS_TEXT if is_unlocked else COLOR_DANGER_TEXT
        icon = "🔓" if is_unlocked else "🔒"
        status_txt = "DOOR UNLOCKED" if is_unlocked else "DOOR LOCKED"

        self.lock_display_box.config(bg=bg_col)
        self.lbl_lock_icon.config(text=icon, bg=bg_col, fg=text_col)
        self.lbl_lock_status.config(text=status_txt, bg=bg_col, fg=text_col)
        self.lbl_door_position.config(bg=bg_col)
        self.lbl_timer_notice.config(bg=bg_col)

        if is_unlocked:
            self._start_relock_countdown(5)
        else:
            if self.auto_relock_after_id:
                self.after_cancel(self.auto_relock_after_id)
                self.auto_relock_after_id = None
            self.lbl_timer_notice.config(text="")

    def _start_relock_countdown(self, seconds):
        if self.auto_relock_after_id:
            self.after_cancel(self.auto_relock_after_id)

        self.relock_countdown = seconds

        def tick():
            if self.relock_countdown > 0:
                self.lbl_timer_notice.config(text=f"Safety auto-relock in {self.relock_countdown}s...")
                self.relock_countdown -= 1
                self.auto_relock_after_id = self.after(1000, tick)
            else:
                if self.selected_room:
                    set_door_state(self.selected_room["id"], "locked", actor="Auto-Relock Safety Timer")
                    self.refresh_all_data()

        tick()

    def _set_physical_door(self, pos):
        self.lbl_door_position.config(text=f"Physical Door: {pos}")
        messagebox.showinfo("Hardware State", f"Physical door position set to: {pos}")

    # --- Actions ---
    def _rotate_super_key(self):
        new_sk = rotate_daily_super_key()
        self.refresh_all_data()
        messagebox.showinfo("Super Key Rotated", f"New Daily Super Key issued:\n{new_sk['plain_key']}\n\nDatabase Hash:\n{new_sk['key_hash']}")

    def _test_unlock(self, method="wifi", user_type="customer"):
        if not self.selected_room:
            messagebox.showwarning("Warning", "Please select a room first.")
            return

        room = self.selected_room
        room_id = room["id"]

        # Determine key to present
        if user_type == "staff":
            sk = get_daily_super_key()
            key_token = sk["plain_key"]
            actor_name = "Staff Member (Simulator)"
        else:
            if not room["active_key"]:
                messagebox.showerror(
                    "No Key",
                    f"Room {room['room_number']} has no active customer key minted (Room is {room['status']}).\n"
                    "Click 'Mint New Regular Key (Check-In)' below to simulate a checked-in guest."
                )
                return
            key_token = room["active_key"]
            actor_name = room["guest_name"] or "Guest (Simulator)"

        # Determine Wi-Fi SSID
        wifi_choice = self.combo_wifi_test.get()
        if wifi_choice == "Matching Room Wi-Fi":
            wifi_ssid = room["wifi_ssid"]
        elif wifi_choice.startswith("Quest_Staff_Secure"):
            wifi_ssid = STAFF_WIFI_SSID
        elif wifi_choice.startswith("Quest_Lobby_Guest_WiFi"):
            wifi_ssid = "Quest_Lobby_Guest_WiFi"
        else:
            wifi_ssid = ""

        granted, msg, details = verify_door_access(
            room_id=room_id,
            key_token=key_token,
            method=method,
            wifi_ssid=wifi_ssid,
            user_type=user_type,
            user_id=999,
            user_name=actor_name
        )

        self.refresh_all_data()

        if granted:
            messagebox.showinfo("Access Granted", f"✅ SUCCESS: {msg}\n\nMethod: {method.upper()}\nKey: {key_token}\nWi-Fi: {wifi_ssid or 'NFC Direct'}")
        else:
            messagebox.showerror("Access Denied", f"❌ DENIED: {msg}\n\nMethod: {method.upper()}\nSimulated Wi-Fi: '{wifi_ssid}'\nRequired Wi-Fi: '{room['wifi_ssid']}'")

    def _test_fake_key(self):
        if not self.selected_room:
            return
        room = self.selected_room
        fake_token = "FAKE-KEY-INTRUDER-9999"
        granted, msg, details = verify_door_access(
            room_id=room["id"],
            key_token=fake_token,
            method="nfc",
            wifi_ssid=room["wifi_ssid"],
            user_type="unknown",
            user_id=0,
            user_name="Unregistered Intruder"
        )
        self.refresh_all_data()
        messagebox.showerror("Security Alert", f"❌ FAKE KEY REJECTED: {msg}\n\nHashed check failed in database.")

    def _test_revoked_key(self):
        if not self.selected_room:
            return
        room = self.selected_room
        revoked_token = "REG-REVOKED-EXPIRED-PREVIOUS"
        granted, msg, details = verify_door_access(
            room_id=room["id"],
            key_token=revoked_token,
            method="wifi",
            wifi_ssid=room["wifi_ssid"],
            user_type="customer",
            user_id=1,
            user_name="Checked-Out Guest"
        )
        self.refresh_all_data()
        messagebox.showerror("Security Alert", f"❌ EXPIRED KEY REJECTED: {msg}\n\nRevoked key cannot unlock doors.")

    def _manual_door_state(self, state):
        if not self.selected_room:
            return
        set_door_state(self.selected_room["id"], state, actor="Testbed Manual Override")
        self.refresh_all_data()

    def _simulate_checkin_mint(self):
        if not self.selected_room:
            return
        room = self.selected_room
        # Mint new regular key for this room
        res = mint_room_key(room["id"], customer_id=1, reservation_id=999)
        self.refresh_all_data()
        messagebox.showinfo(
            "Check-In Simulated",
            f"✅ New Regular Key Minted for Room {room['room_number']}:\n\n"
            f"Plain Token: {res['plain_key']}\n"
            f"DB Key Hash: {res['key_hash']}\n\n"
            f"Previous regular keys for this suite are now REVOKED."
        )

    def _simulate_checkout_revoke(self):
        if not self.selected_room:
            return
        room = self.selected_room
        revoke_room_key(room["id"])
        self.refresh_all_data()
        messagebox.showinfo(
            "Checkout Simulated",
            f"🔒 Room {room['room_number']} regular key is now REVOKED.\nDoor is locked."
        )


if __name__ == "__main__":
    app = DoorSimulatorApp()
    app.mainloop()

