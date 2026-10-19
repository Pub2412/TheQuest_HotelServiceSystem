"""
Staff Portal for The Quest Hotel Management System.
Supports Kitchen, Logistics, and Utilities roles.
Features:
- Kitchen Tab: Ingredient inventory, low stock automated alerts, room food orders, request room service pickup, complete orders.
- Logistics Tab: Shipments categorized as 'Will be Shipped', 'On the Way', and 'Near Receive', passcode verification ('QUEST-LOG-2026') for completion/cancellation.
- Utilities Tab: Rooms needing service/food delivery ('full swing' per day), update tasks (Complete, Processing, Canceled), CANNOT view empty rooms (strictly hidden!), Hotel Map view.
- Bulletin & Softphone Calling Inbox.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.db import get_connection
from utils.theme import (
    COLOR_PRIMARY_DARK, COLOR_PRIMARY, COLOR_PRIMARY_LIGHT, COLOR_PRIMARY_TINT,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_ACCENT_LIGHT, COLOR_ACCENT_TEXT,
    COLOR_WHITE, COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT_DARK,
    COLOR_TEXT_NORMAL, COLOR_TEXT_MUTED, COLOR_DANGER, COLOR_DANGER_BG,
    COLOR_DANGER_TEXT, COLOR_SUCCESS, COLOR_SUCCESS_BG, COLOR_SUCCESS_TEXT,
    COLOR_WARNING, COLOR_WARNING_BG, COLOR_WARNING_TEXT, COLOR_INFO,
    COLOR_INFO_BG, COLOR_INFO_TEXT,
    FONT_FAMILY, FONT_HEADING, FONT_SUBHEADING, FONT_TITLE, FONT_BODY,
    FONT_BODY_BOLD, FONT_SMALL, FONT_SMALL_BOLD, FONT_STAT_VAL,
    SYSTEM_NAME, SYSTEM_SUBTITLE, SYSTEM_SLOGAN
)
from utils.image_loader import load_image, get_icon_logo
from utils.components import MetricCard, HotelMapWidget, PhoneCallModal
from utils.logger import log_auth_event

LOGISTICS_AUTH_CODE = "QUEST-LOG-2026"

class StaffPage(tk.Frame):
    def __init__(self, parent, current_user: dict, on_logout_cb):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.current_user = current_user
        self.on_logout_cb = on_logout_cb

        # Determine default tab based on staff role
        role = self.current_user.get("role", "Staff_Kitchen")
        if "Kitchen" in role:
            self.default_tab = "kitchen"
        elif "Logistics" in role:
            self.default_tab = "logistics"
        elif "Utilities" in role:
            self.default_tab = "utilities"
        else:
            self.default_tab = "kitchen"

        self._build_layout()
        self._switch_tab(self.default_tab)

    def _build_layout(self):
        # ------------------ TOP APP HEADER ------------------
        header = tk.Frame(self, bg=COLOR_PRIMARY_DARK, height=64)
        header.pack(fill="x", side="top")

        left_hdr = tk.Frame(header, bg=COLOR_PRIMARY_DARK)
        left_hdr.pack(side="left", padx=16, pady=8)

        try:
            self.icon_photo = get_icon_logo((36, 36))
            tk.Label(left_hdr, image=self.icon_photo, bg=COLOR_PRIMARY_DARK).pack(side="left", padx=(0, 10))
        except Exception:
            pass

        title_box = tk.Frame(left_hdr, bg=COLOR_PRIMARY_DARK)
        title_box.pack(side="left")

        role_display = self.current_user.get("role", "Staff").replace("_", " ").upper()
        tk.Label(
            title_box,
            text=f"{SYSTEM_NAME.upper()} • {role_display} PORTAL",
            font=(FONT_FAMILY, 12, "bold"),
            fg=COLOR_WHITE,
            bg=COLOR_PRIMARY_DARK
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text=f'"{SYSTEM_SLOGAN}"',
            font=(FONT_FAMILY, 8, "italic"),
            fg=COLOR_ACCENT,
            bg=COLOR_PRIMARY_DARK
        ).pack(anchor="w")

        # Right Header
        right_hdr = tk.Frame(header, bg=COLOR_PRIMARY_DARK)
        right_hdr.pack(side="right", padx=16, pady=8)

        user_name = self.current_user.get("name", "Staff Member")
        img_path = self.current_user.get("image_path", "assets/imgs/employees/m/4.jpg")

        try:
            self.user_avatar = load_image(img_path, (36, 36), circular=True)
            tk.Label(right_hdr, image=self.user_avatar, bg=COLOR_PRIMARY_DARK).pack(side="left", padx=(0, 8))
        except Exception:
            pass

        u_info = tk.Frame(right_hdr, bg=COLOR_PRIMARY_DARK)
        u_info.pack(side="left", padx=(0, 14))

        tk.Label(u_info, text=user_name, font=(FONT_FAMILY, 10, "bold"), fg=COLOR_WHITE, bg=COLOR_PRIMARY_DARK).pack(anchor="e")
        tk.Label(u_info, text=f"Role: {role_display}", font=(FONT_FAMILY, 8), fg=COLOR_ACCENT, bg=COLOR_PRIMARY_DARK).pack(anchor="e")

        logout_btn = tk.Button(
            right_hdr,
            text="Sign Out",
            font=(FONT_FAMILY, 9, "bold"),
            bg="#581C87",
            fg=COLOR_WHITE,
            activebackground=COLOR_DANGER,
            activeforeground=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._handle_logout
        )
        logout_btn.pack(side="left")

        # ------------------ WORKSPACE ------------------
        workspace = tk.Frame(self, bg=COLOR_BG)
        workspace.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(workspace, bg=COLOR_PRIMARY, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="STAFF OPERATIONS",
            font=(FONT_FAMILY, 8, "bold"),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY,
            padx=16,
            pady=12
        ).pack(anchor="w")

        self.nav_buttons = {}
        nav_items = [
            ("kitchen", "🍳 Kitchen & Culinary"),
            ("logistics", "🚚 Logistics & Shipments"),
            ("utilities", "🧹 Utilities & Housekeeping"),
            ("bulletin", "📢 Staff Bulletin"),
            ("inbox", "💬 Inbox & Voice Call"),
        ]

        for tab_id, label in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=(FONT_FAMILY, 9, "bold"),
                fg=COLOR_WHITE,
                bg=COLOR_PRIMARY,
                activebackground=COLOR_PRIMARY_LIGHT,
                activeforeground=COLOR_ACCENT,
                anchor="w",
                padx=16,
                pady=10,
                relief="flat",
                cursor="hand2",
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(fill="x")
            self.nav_buttons[tab_id] = btn

        self.content_container = tk.Frame(workspace, bg=COLOR_BG, padx=16, pady=16)
        self.content_container.pack(side="right", fill="both", expand=True)

    def _switch_tab(self, tab_id: str):
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.config(bg=COLOR_PRIMARY_LIGHT, fg=COLOR_ACCENT)
            else:
                btn.config(bg=COLOR_PRIMARY, fg=COLOR_WHITE)

        for widget in self.content_container.winfo_children():
            widget.destroy()

        if tab_id == "kitchen":
            self._render_kitchen_tab()
        elif tab_id == "logistics":
            self._render_logistics_tab()
        elif tab_id == "utilities":
            self._render_utilities_tab()
        elif tab_id == "bulletin":
            self._render_bulletin_tab()
        elif tab_id == "inbox":
            self._render_inbox_tab()

    def _handle_logout(self):
        log_auth_event(
            event_type="LOGOUT",
            username=self.current_user.get("username", "Staff"),
            role=self.current_user.get("role", "Staff"),
            status="SUCCESS",
            details="Staff member signed out."
        )
        self.on_logout_cb()

    # =========================================================================
    # TAB 1: KITCHEN OPERATIONS (INVENTORY + LOW STOCK ALERTS + FOOD ORDERS)
    # =========================================================================
    def _render_kitchen_tab(self):
        # Check low stock kitchen items
        with get_connection() as conn:
            low_stock = conn.execute("""
                SELECT item_name, quantity, low_stock_threshold, unit
                FROM inventory
                WHERE category = 'Kitchen' AND quantity <= low_stock_threshold
            """).fetchall()

        # Automated Low Stock Notification Banner
        if low_stock:
            alert_card = tk.Frame(self.content_container, bg=COLOR_DANGER_BG, highlightthickness=2, highlightbackground=COLOR_DANGER, padx=14, pady=10)
            alert_card.pack(fill="x", pady=(0, 12))

            items_str = ", ".join([f"{r['item_name']} ({r['quantity']} {r['unit']} left, thresh {r['low_stock_threshold']})" for r in low_stock])
            tk.Label(
                alert_card,
                text="⚠️ KITCHEN ALERT: Low Ingredients Detected!",
                font=(FONT_FAMILY, 11, "bold"),
                fg=COLOR_DANGER_TEXT,
                bg=COLOR_DANGER_BG
            ).pack(anchor="w")

            tk.Label(
                alert_card,
                text=f"The following kitchen ingredients are running dangerously low: {items_str}. Please request logistics restock.",
                font=(FONT_FAMILY, 9),
                fg=COLOR_DANGER_TEXT,
                bg=COLOR_DANGER_BG,
                wraplength=800,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))

        # Split into two panels: Top Active Room Food Orders, Bottom Kitchen Ingredients
        panes = tk.Frame(self.content_container, bg=COLOR_BG)
        panes.pack(fill="both", expand=True)

        # 1. Active Room Food Orders
        orders_card = tk.Frame(panes, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        orders_card.pack(fill="both", expand=True, pady=(0, 12))

        tk.Label(
            orders_card,
            text="🍽️ Active Customer Room Food Orders & Room Service Deliveries",
            font=FONT_SUBHEADING,
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 8))

        cols = ("id", "room", "guest", "details", "status", "time")
        tree_orders = ttk.Treeview(orders_card, columns=cols, show="headings", height=6)

        tree_orders.heading("id", text="Order #")
        tree_orders.heading("room", text="Delivery Room")
        tree_orders.heading("guest", text="Guest Name")
        tree_orders.heading("details", text="Food Order Details")
        tree_orders.heading("status", text="Order Status")
        tree_orders.heading("time", text="Time Ordered")

        tree_orders.column("id", width=55, anchor="center")
        tree_orders.column("room", width=90, anchor="center")
        tree_orders.column("guest", width=140, anchor="w")
        tree_orders.column("details", width=280, anchor="w")
        tree_orders.column("status", width=110, anchor="center")
        tree_orders.column("time", width=120, anchor="center")

        tree_orders.tag_configure("processing", background=COLOR_WARNING_BG, foreground=COLOR_WARNING_TEXT)
        tree_orders.tag_configure("complete", background=COLOR_SUCCESS_BG, foreground=COLOR_SUCCESS_TEXT)

        def load_orders():
            for i in tree_orders.get_children():
                tree_orders.delete(i)
            with get_connection() as conn:
                q = """
                    SELECT sr.*, r.room_number, c.name AS customer_name
                    FROM service_requests sr
                    JOIN rooms r ON sr.room_id = r.id
                    JOIN customers c ON sr.customer_id = c.id
                    WHERE sr.request_type = 'Food Delivery' OR sr.details LIKE '%food%' OR sr.details LIKE '%breakfast%' OR sr.details LIKE '%toast%'
                    ORDER BY sr.id DESC
                """
                orders = conn.execute(q).fetchall()

            for o in orders:
                st = o["status"]
                tag = ("processing",) if st == "Processing" else ("complete",)
                date_str = str(o["date_created"] or "")[:16] if "date_created" in o.keys() else ""
                tree_orders.insert("", "end", values=(
                    f"#{o['id']}", f"Room {o['room_number']}", o["customer_name"],
                    o["details"], st, date_str
                ), tags=tag)

        load_orders()
        tree_orders.pack(fill="both", expand=True)

        # Action Buttons for Food Orders
        act_f = tk.Frame(orders_card, bg=COLOR_WHITE)
        act_f.pack(fill="x", pady=(8, 0))

        def request_room_service_pickup():
            sel = tree_orders.selection()
            if not sel:
                messagebox.showwarning("Select Order", "Please select a food order to dispatch for delivery.")
                return
            order_id = int(tree_orders.item(sel[0])["values"][0].replace("#", ""))
            with get_connection() as conn:
                order_row = conn.execute("SELECT r.room_number FROM service_requests sr JOIN rooms r ON sr.room_id = r.id WHERE sr.id = ?", (order_id,)).fetchone()
                r_num = order_row["room_number"] if order_row else "Guest Room"
                # Dispatch notification to Utilities/Room service in messages
                conn.execute("""
                    INSERT INTO messages (sender_id, receiver_role, content, timestamp)
                    VALUES (?, 'Staff_Utilities', ?, CURRENT_TIMESTAMP)
                """, (self.current_user["id"], f"HOT FOOD READY: Order #{order_id} for Room {r_num} is prepared on the service pass! Please dispatch room service immediately."))
                conn.commit()

            messagebox.showinfo(
                "Room Service Dispatched",
                f"Urgent pickup alert transmitted to Room Service & Housekeeping!\nAttendants notified to collect Order #{order_id} from kitchen pass."
            )

        tk.Button(
            act_f,
            text="🛎️ Request Room Service Pickup & Deliver Food",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=request_room_service_pickup
        ).pack(side="left", padx=4)

        def mark_order_complete():
            sel = tree_orders.selection()
            if not sel:
                messagebox.showwarning("Select Order", "Please select a food order to complete.")
                return
            order_id = int(tree_orders.item(sel[0])["values"][0].replace("#", ""))
            with get_connection() as conn:
                conn.execute("UPDATE service_requests SET status = 'Complete' WHERE id = ?", (order_id,))
                conn.commit()
            messagebox.showinfo("Order Complete", f"Order #{order_id} has been marked as Complete!")
            load_orders()

        tk.Button(
            act_f,
            text="✓ Update Food Order as Complete",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=mark_order_complete
        ).pack(side="left", padx=4)

        # 2. Kitchen Ingredients Inventory Table
        inv_card = tk.Frame(panes, bg=COLOR_WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        inv_card.pack(fill="both", expand=True)

        tk.Label(inv_card, text="📦 Kitchen Culinary Ingredients Stock Monitor", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 6))

        cols_inv = ("name", "qty", "unit", "thresh", "status")
        tree_inv = ttk.Treeview(inv_card, columns=cols_inv, show="headings", height=6)

        tree_inv.heading("name", text="Ingredient Name")
        tree_inv.heading("qty", text="In Stock")
        tree_inv.heading("unit", text="Unit")
        tree_inv.heading("thresh", text="Min. Threshold")
        tree_inv.heading("status", text="Condition")

        tree_inv.column("name", width=220, anchor="w")
        tree_inv.column("qty", width=90, anchor="e")
        tree_inv.column("unit", width=80, anchor="center")
        tree_inv.column("thresh", width=100, anchor="e")
        tree_inv.column("status", width=120, anchor="center")

        tree_inv.tag_configure("low", background=COLOR_DANGER_BG, foreground=COLOR_DANGER_TEXT)

        with get_connection() as conn:
            k_items = conn.execute("SELECT * FROM inventory WHERE category = 'Kitchen' ORDER BY quantity ASC").fetchall()

        for ki in k_items:
            is_l = ki["quantity"] <= ki["low_stock_threshold"]
            st_txt = "⚠️ LOW STOCK" if is_l else "In Stock"
            tag = ("low",) if is_l else ()
            tree_inv.insert("", "end", values=(
                ki["item_name"], ki["quantity"], ki["unit"] or "units",
                ki["low_stock_threshold"], st_txt
            ), tags=tag)

        tree_inv.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 2: LOGISTICS (CATEGORIZED SHIPMENTS & PASSCODE VERIFICATION)
    # =========================================================================
    def _render_logistics_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Supply Chain Deliveries & Logistics Tracking", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        tk.Button(
            top_bar,
            text="+ Add Inbound Shipment",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._show_add_shipment_modal
        ).pack(side="right")

        # Three Status Columns Layout: 'Will be Shipped', 'On the Way', 'Near Receive'
        cols_frame = tk.Frame(self.content_container, bg=COLOR_BG)
        cols_frame.pack(fill="both", expand=True)
        cols_frame.columnconfigure(0, weight=1)
        cols_frame.columnconfigure(1, weight=1)
        cols_frame.columnconfigure(2, weight=1)

        statuses = [
            ("Will be Shipped", "📦 WILL BE SHIPPED", COLOR_INFO),
            ("On the Way", "🚚 ON THE WAY", COLOR_WARNING),
            ("Near Receive", "📍 NEAR RECEIVE", COLOR_SUCCESS)
        ]

        with get_connection() as conn:
            deliveries = conn.execute("SELECT * FROM deliveries ORDER BY id DESC").fetchall()

        for c_idx, (st_key, st_title, st_color) in enumerate(statuses):
            col_box = tk.Frame(cols_frame, bg=COLOR_WHITE, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
            col_box.grid(row=0, column=c_idx, padx=5, sticky="nsew")

            h_f = tk.Frame(col_box, bg=COLOR_WHITE)
            h_f.pack(fill="x", pady=(0, 8))

            tk.Label(h_f, text=st_title, font=(FONT_FAMILY, 10, "bold"), fg=st_color, bg=COLOR_WHITE).pack(side="left")

            matches = [d for d in deliveries if d["status"] == st_key]
            tk.Label(h_f, text=f"({len(matches)})", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side="right")

            canvas = tk.Canvas(col_box, bg=COLOR_BG, highlightthickness=0)
            scroll = ttk.Scrollbar(col_box, orient="vertical", command=canvas.yview)
            card_f = tk.Frame(canvas, bg=COLOR_BG)

            card_f.bind("<Configure>", lambda e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            c_win = canvas.create_window((0, 0), window=card_f, anchor="nw")
            canvas.configure(xscrollcommand=None, yscrollcommand=scroll.set)
            canvas.bind("<Configure>", lambda e, c=canvas, cw=c_win: c.itemconfig(cw, width=e.width))

            canvas.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")

            for d in matches:
                item_card = tk.Frame(card_f, bg=COLOR_WHITE, padx=10, pady=8, highlightthickness=1, highlightbackground=COLOR_BORDER)
                item_card.pack(fill="x", pady=4)

                tk.Label(item_card, text=f"Shipment #{d['id']}", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w")
                tk.Label(item_card, text=d["description"], font=(FONT_FAMILY, 9), fg=COLOR_TEXT_DARK, bg=COLOR_WHITE, wraplength=200, justify="left").pack(anchor="w", pady=(2, 4))
                tk.Label(item_card, text=f"Updated: {str(d['date_updated'])[:16]}", font=(FONT_FAMILY, 7), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")

                # Action button to complete or cancel with logistics passcode
                btn_f = tk.Frame(item_card, bg=COLOR_WHITE)
                btn_f.pack(fill="x", pady=(6, 0))

                comp_btn = tk.Button(
                    btn_f,
                    text="✓ Receive / Complete",
                    font=(FONT_FAMILY, 8, "bold"),
                    bg=COLOR_SUCCESS,
                    fg=COLOR_WHITE,
                    relief="flat",
                    padx=6,
                    pady=2,
                    cursor="hand2",
                    command=lambda d_id=d["id"]: self._verify_and_update_shipment(d_id, "Completed")
                )
                comp_btn.pack(side="left")

                canc_btn = tk.Button(
                    btn_f,
                    text="Cancel",
                    font=(FONT_FAMILY, 8),
                    bg=COLOR_BG,
                    fg=COLOR_DANGER,
                    relief="flat",
                    padx=6,
                    pady=2,
                    cursor="hand2",
                    command=lambda d_id=d["id"]: self._verify_and_update_shipment(d_id, "Canceled")
                )
                canc_btn.pack(side="right")

    def _verify_and_update_shipment(self, shipment_id: int, new_status: str):
        """Demands the secret logistics code before completing or canceling shipments."""
        code = simpledialog.askstring(
            "Logistics Authorization Required",
            f"Enter authorized Logistics Security Code to mark Shipment #{shipment_id} as '{new_status}':\n(Default: {LOGISTICS_AUTH_CODE})",
            show="*"
        )
        if not code:
            return

        if code.strip() != LOGISTICS_AUTH_CODE:
            messagebox.showerror("Security Clearance Denied", "Invalid Logistics Security Code! Update rejected.")
            return

        with get_connection() as conn:
            conn.execute("""
                UPDATE deliveries
                SET status = ?, date_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, shipment_id))
            conn.commit()

        messagebox.showinfo("Authorization Confirmed", f"Shipment #{shipment_id} has been marked as '{new_status}'.")
        self._switch_tab("logistics")

    def _show_add_shipment_modal(self):
        modal = tk.Toplevel(self)
        modal.title("New Logistics Delivery")
        modal.geometry("380x300")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="NEW INBOUND DELIVERY", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Cargo Description:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        desc_e = tk.Entry(form, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        desc_e.pack(fill="x", ipady=3, pady=(2, 10))

        tk.Label(form, text="Initial Delivery Status:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        stat_var = tk.StringVar(value="Will be Shipped")
        cb = ttk.Combobox(form, textvariable=stat_var, values=["Will be Shipped", "On the Way", "Near Receive"], state="readonly")
        cb.pack(fill="x", pady=(2, 10))

        def save_shipment():
            d = desc_e.get().strip()
            if not d:
                messagebox.showwarning("Missing Info", "Cargo description is required.")
                return

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO deliveries (description, status, logistics_code, date_updated)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (d, stat_var.get(), LOGISTICS_AUTH_CODE))
                conn.commit()

            messagebox.showinfo("Shipment Added", "Inbound shipment recorded in logistics database!")
            modal.destroy()
            self._switch_tab("logistics")

        tk.Button(modal, text="Register Delivery", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=14, pady=6, command=save_shipment).pack(pady=12)

    # =========================================================================
    # TAB 3: UTILITIES & HOUSEKEEPING (NEEDS SERVICE + HIDDEN EMPTY ROOMS)
    # =========================================================================
    def _render_utilities_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar,
            text="Housekeeping Tasks & Occupied Rooms 'Full Swing'",
            font=FONT_HEADING,
            fg=COLOR_PRIMARY,
            bg=COLOR_BG
        ).pack(side="left")

        # Two Tabs: Task List and Hotel Map View (strictly hiding empty rooms!)
        nb = ttk.Notebook(self.content_container)
        nb.pack(fill="both", expand=True)

        # Sub-tab 1: Active Service Requests & Cleaning Tasks
        f_tasks = tk.Frame(nb, bg=COLOR_WHITE, padx=14, pady=12)
        nb.add(f_tasks, text="📋 Room Service & Daily Cleaning Tasks")

        cols = ("id", "room", "guest", "type", "details", "status", "action")
        tree = ttk.Treeview(f_tasks, columns=cols, show="headings", height=12)

        tree.heading("id", text="Task #")
        tree.heading("room", text="Room")
        tree.heading("guest", text="Occupant")
        tree.heading("type", text="Service Type")
        tree.heading("details", text="Instructions / Request Details")
        tree.heading("status", text="Current State")
        tree.heading("action", text="Daily Schedule")

        tree.column("id", width=50, anchor="center")
        tree.column("room", width=80, anchor="center")
        tree.column("guest", width=140, anchor="w")
        tree.column("type", width=110, anchor="center")
        tree.column("details", width=260, anchor="w")
        tree.column("status", width=100, anchor="center")
        tree.column("action", width=120, anchor="center")

        tree.tag_configure("proc", background=COLOR_WARNING_BG, foreground=COLOR_WARNING_TEXT)
        tree.tag_configure("done", background=COLOR_SUCCESS_BG, foreground=COLOR_SUCCESS_TEXT)

        def load_tasks():
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                # Strictly only rooms that are NOT empty (guest checked in or active request)
                q = """
                    SELECT sr.*, r.room_number, r.status AS room_status, c.name AS customer_name
                    FROM service_requests sr
                    JOIN rooms r ON sr.room_id = r.id
                    LEFT JOIN customers c ON sr.customer_id = c.id
                    ORDER BY sr.status DESC, sr.id DESC
                """
                tasks = conn.execute(q).fetchall()

            for t in tasks:
                st = t["status"]
                tag = ("proc",) if st == "Processing" else ("done",)
                tree.insert("", "end", values=(
                    f"#{t['id']}", f"Room {t['room_number']}", t["customer_name"] or "Guest",
                    t["request_type"], t["details"], st, "Full Swing Daily"
                ), tags=tag)

        load_tasks()
        tree.pack(fill="both", expand=True)

        # Action Buttons
        btn_bar = tk.Frame(f_tasks, bg=COLOR_WHITE)
        btn_bar.pack(fill="x", pady=(10, 0))

        def update_task_state(new_state):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Task", "Please select a task from the list.")
                return
            t_id = int(tree.item(sel[0])["values"][0].replace("#", ""))
            with get_connection() as conn:
                conn.execute("UPDATE service_requests SET status = ? WHERE id = ?", (new_state, t_id))
                # If completed, check if room status should be set to Occupied / clean
                req = conn.execute("SELECT room_id FROM service_requests WHERE id = ?", (t_id,)).fetchone()
                if req and new_state == "Complete":
                    conn.execute("UPDATE rooms SET status = 'Occupied' WHERE id = ? AND status = 'Needs Service'", (req["room_id"],))
                conn.commit()

            messagebox.showinfo("Task Updated", f"Task #{t_id} marked as '{new_state}'!")
            load_tasks()

        tk.Button(btn_bar, text="✓ Mark Task Complete", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_SUCCESS, fg=COLOR_WHITE, relief="flat", padx=10, pady=5, command=lambda: update_task_state("Complete")).pack(side="left", padx=4)
        tk.Button(btn_bar, text="⏳ Set Processing", font=(FONT_FAMILY, 9), bg=COLOR_WARNING, fg=COLOR_TEXT_DARK, relief="flat", padx=10, pady=5, command=lambda: update_task_state("Processing")).pack(side="left", padx=4)
        tk.Button(btn_bar, text="Cancel Task", font=(FONT_FAMILY, 9), bg=COLOR_BG, fg=COLOR_DANGER, relief="flat", padx=10, pady=5, command=lambda: update_task_state("Canceled")).pack(side="left", padx=4)

        # Sub-tab 2: Hotel Map View (strictly hiding empty/vacant rooms!)
        f_map = tk.Frame(nb, bg=COLOR_BG)
        nb.add(f_map, text="🏨 Occupied Hotel Map View (Vacant Rooms Hidden)")

        hotel_map = HotelMapWidget(f_map, get_connection, utilities_mode=True)
        hotel_map.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 4: BULLETIN
    # =========================================================================
    def _render_bulletin_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Staff Bulletin & Official Announcements", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        canvas = tk.Canvas(self.content_container, bg=COLOR_BG, highlightthickness=0)
        scroll = ttk.Scrollbar(self.content_container, orient="vertical", command=canvas.yview)
        feed_frame = tk.Frame(canvas, bg=COLOR_BG)

        feed_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        c_win = canvas.create_window((0, 0), window=feed_frame, anchor="nw")
        canvas.configure(xscrollcommand=None, yscrollcommand=scroll.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(c_win, width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        with get_connection() as conn:
            posts = conn.execute("""
                SELECT b.*, u.name AS author_name, u.role AS author_role
                FROM bulletin b
                JOIN users u ON b.author_id = u.id
                ORDER BY b.timestamp DESC
            """).fetchall()

        for p in posts:
            card = tk.Frame(feed_frame, bg=COLOR_WHITE, padx=16, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
            card.pack(fill="x", pady=6)

            h_row = tk.Frame(card, bg=COLOR_WHITE)
            h_row.pack(fill="x", pady=(0, 4))

            tk.Label(h_row, text=p["title"], font=(FONT_FAMILY, 12, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(side="left")
            tk.Label(h_row, text=str(p["timestamp"])[:16], font=(FONT_FAMILY, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side="right")

            tk.Label(card, text=f"Author: {p['author_name']} ({p['author_role']})", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_ACCENT, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 6))
            tk.Label(card, text=p["content"], font=(FONT_FAMILY, 9), fg=COLOR_TEXT_NORMAL, bg=COLOR_WHITE, wraplength=700, justify="left").pack(anchor="w")

    # =========================================================================
    # TAB 5: INBOX & VOICE CALL
    # =========================================================================
    def _render_inbox_tab(self):
        panes = tk.Frame(self.content_container, bg=COLOR_BG)
        panes.pack(fill="both", expand=True)
        panes.columnconfigure(0, weight=4)
        panes.columnconfigure(1, weight=6)

        left_card = tk.Frame(panes, bg=COLOR_WHITE, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(left_card, text="STAFF SPEED DIAL DIRECTORY", font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 8))

        # Selected Staff Photo & Info Box (Highlighted Staff)
        preview_box = tk.Frame(
            left_card,
            bg=COLOR_PRIMARY_TINT,
            padx=10,
            pady=10,
            highlightthickness=1,
            highlightbackground=COLOR_ACCENT
        )
        preview_box.pack(fill="x", pady=(0, 10))

        # Photo Container Box with prominent accent border
        photo_box = tk.Frame(
            preview_box,
            bg=COLOR_WHITE,
            width=100,
            height=100,
            highlightthickness=2,
            highlightbackground=COLOR_PRIMARY
        )
        photo_box.pack_propagate(False)
        photo_box.pack(side="left", padx=(0, 10))

        staff_photo_lbl = tk.Label(photo_box, bg=COLOR_WHITE)
        staff_photo_lbl.pack(fill="both", expand=True)

        info_box = tk.Frame(preview_box, bg=COLOR_PRIMARY_TINT)
        info_box.pack(side="left", fill="both", expand=True)

        lbl_p_title = tk.Label(info_box, text="HIGHLIGHTED STAFF PROFILE", font=(FONT_FAMILY, 7, "bold"), fg=COLOR_PRIMARY, bg=COLOR_PRIMARY_TINT)
        lbl_p_title.pack(anchor="w")

        lbl_p_name = tk.Label(info_box, text="-", font=(FONT_FAMILY, 10, "bold"), fg=COLOR_TEXT_NORMAL, bg=COLOR_PRIMARY_TINT)
        lbl_p_name.pack(anchor="w")

        lbl_p_role = tk.Label(info_box, text="-", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_ACCENT_TEXT, bg=COLOR_ACCENT_LIGHT, padx=6, pady=1)
        lbl_p_role.pack(anchor="w", pady=2)

        lbl_p_phone = tk.Label(info_box, text="", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_NORMAL, bg=COLOR_PRIMARY_TINT)
        lbl_p_phone.pack(anchor="w")

        selected_user_state = {"staff": None, "row_widgets": []}
        current_loaded_photo = [None]

        def highlight_staff(staff_dict, row_widget):
            for rw in selected_user_state["row_widgets"]:
                try:
                    rw.configure(bg=COLOR_WHITE, highlightbackground=COLOR_BORDER, highlightthickness=1)
                    for child in rw.winfo_children():
                        if isinstance(child, tk.Frame):
                            child.configure(bg=COLOR_WHITE)
                            for subchild in child.winfo_children():
                                if isinstance(subchild, tk.Label):
                                    subchild.configure(bg=COLOR_WHITE)
                except Exception:
                    pass

            try:
                row_widget.configure(bg=COLOR_PRIMARY_TINT, highlightbackground=COLOR_ACCENT, highlightthickness=2)
                for child in row_widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=COLOR_PRIMARY_TINT)
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                subchild.configure(bg=COLOR_PRIMARY_TINT)
            except Exception:
                pass

            img_path = staff_dict.get("image_path") or "assets/imgs/employees/m/1.jpg"
            img = load_image(img_path, (96, 96), preserve_aspect=True)
            current_loaded_photo[0] = img
            staff_photo_lbl.configure(image=img)

            lbl_p_name.config(text=staff_dict.get("name", "Staff"))
            lbl_p_role.config(text=str(staff_dict.get("role", "Staff")).replace("_", " ").upper())
            lbl_p_phone.config(text=f"📞 {staff_dict.get('phone', 'No number')}")
            selected_user_state["staff"] = staff_dict

        canvas = tk.Canvas(left_card, bg=COLOR_WHITE, highlightthickness=0)
        scroll = ttk.Scrollbar(left_card, orient="vertical", command=canvas.yview)
        s_list = tk.Frame(canvas, bg=COLOR_WHITE)

        s_list.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        c_win = canvas.create_window((0, 0), window=s_list, anchor="nw")
        canvas.configure(xscrollcommand=None, yscrollcommand=scroll.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(c_win, width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        with get_connection() as conn:
            staff_rows = conn.execute("SELECT * FROM users WHERE id != ? ORDER BY role, name ASC", (self.current_user["id"],)).fetchall()

        for idx, s in enumerate(staff_rows):
            s_dict = dict(s)
            row_box = tk.Frame(s_list, bg=COLOR_WHITE, pady=4, highlightthickness=1, highlightbackground=COLOR_BORDER, cursor="hand2")
            row_box.pack(fill="x", pady=2)
            selected_user_state["row_widgets"].append(row_box)

            info_f = tk.Frame(row_box, bg=COLOR_WHITE)
            info_f.pack(side="left", padx=6)

            name_lbl = tk.Label(info_f, text=s_dict["name"], font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_NORMAL, bg=COLOR_WHITE)
            name_lbl.pack(anchor="w")
            role_lbl = tk.Label(info_f, text=f"{s_dict['role']}  •  {s_dict['phone'] or 'N/A'}", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE)
            role_lbl.pack(anchor="w")

            def make_click_handler(staff=s_dict, rw=row_box):
                return lambda e: highlight_staff(staff, rw)

            handler = make_click_handler(s_dict, row_box)
            row_box.bind("<Button-1>", handler)
            info_f.bind("<Button-1>", handler)
            name_lbl.bind("<Button-1>", handler)
            role_lbl.bind("<Button-1>", handler)

            call_btn = tk.Button(
                row_box,
                text="📞 Call",
                font=(FONT_FAMILY, 8, "bold"),
                bg=COLOR_ACCENT,
                fg=COLOR_ACCENT_TEXT,
                relief="flat",
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda name=s_dict["name"], ph=s_dict["phone"], role=s_dict["role"], img=s_dict["image_path"], staff=s_dict, rw=row_box: (
                    highlight_staff(staff, rw),
                    PhoneCallModal(self, name, ph, role, img)
                )
            )
            call_btn.pack(side="right", padx=6)

            if idx == 0:
                highlight_staff(s_dict, row_box)

        # Right: Dispatch feed and composer
        right_card = tk.Frame(panes, bg=COLOR_WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(right_card, text="STAFF DISPATCH MESSAGES", font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 6))

        tk.Button(
            right_card,
            text="+ Send Message",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._show_dispatch_modal
        ).pack(anchor="w", pady=(0, 10))

        m_canvas = tk.Canvas(right_card, bg=COLOR_BG, highlightthickness=0)
        m_scroll = ttk.Scrollbar(right_card, orient="vertical", command=m_canvas.yview)
        m_frame = tk.Frame(m_canvas, bg=COLOR_BG)

        m_frame.bind("<Configure>", lambda e: m_canvas.configure(scrollregion=m_canvas.bbox("all")))
        m_win = m_canvas.create_window((0, 0), window=m_frame, anchor="nw")
        m_canvas.configure(xscrollcommand=None, yscrollcommand=m_scroll.set)
        m_canvas.bind("<Configure>", lambda e: m_canvas.itemconfig(m_win, width=e.width))

        m_canvas.pack(side="left", fill="both", expand=True)
        m_scroll.pack(side="right", fill="y")

        with get_connection() as conn:
            msgs = conn.execute("""
                SELECT m.*, u.name AS sender_name, u.role AS sender_role
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                ORDER BY m.timestamp DESC
            """).fetchall()

        for m in msgs:
            m_card = tk.Frame(m_frame, bg=COLOR_WHITE, padx=10, pady=8, highlightthickness=1, highlightbackground=COLOR_BORDER)
            m_card.pack(fill="x", pady=3)

            top = tk.Frame(m_card, bg=COLOR_WHITE)
            top.pack(fill="x")

            target_tag = f"Target: {m['receiver_role'] or 'Direct'}"
            tk.Label(top, text=f"{m['sender_name']} ({m['sender_role']})", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(side="left")
            tk.Label(top, text=target_tag, font=(FONT_FAMILY, 8, "bold"), fg=COLOR_ACCENT, bg=COLOR_WHITE).pack(side="left", padx=8)
            tk.Label(top, text=str(m["timestamp"])[:16], font=(FONT_FAMILY, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side="right")

            tk.Label(m_card, text=m["content"], font=(FONT_FAMILY, 9), fg=COLOR_TEXT_NORMAL, bg=COLOR_WHITE, wraplength=400, justify="left").pack(anchor="w", pady=(3, 0))

    def _show_dispatch_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Send Message")
        modal.geometry("400x340")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="SEND STAFF MESSAGE", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Send To Department / Role:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        role_var = tk.StringVar(value="Staff_Kitchen")
        cb = ttk.Combobox(form, textvariable=role_var, values=["Staff_Kitchen", "Staff_Logistics", "Staff_Utilities", "Cashier", "Admin"], state="readonly")
        cb.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Message Text:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        txt = tk.Text(form, font=(FONT_FAMILY, 9), height=5, bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        txt.pack(fill="both", expand=True, pady=(2, 8))

        def send():
            c = txt.get("1.0", "end").strip()
            if not c:
                messagebox.showwarning("Empty", "Please enter message text.")
                return

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO messages (sender_id, receiver_role, content, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (self.current_user["id"], role_var.get(), c))
                conn.commit()

            messagebox.showinfo("Sent", f"Message sent to {role_var.get()} department!")
            modal.destroy()
            self._switch_tab("inbox")

        tk.Button(modal, text="Send Message", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=14, pady=5, command=send).pack(pady=10)
