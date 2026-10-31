"""
Cashier Portal for The Quest Hotel Management System.
Features:
- Customer Reservations (New Booking, Check-In, Check-Out, Cancellation, Room Changes)
- Hotel Floor Map Visualizer (Synchronized room occupancy)
- Customer Directory & Loyalty Points View
- Employee Bulletin Announcements
- Employee Inbox & Interactive Voice Softphone Calling
- Slogan and Logo presentation in Royal Purple & Gold
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from database.db import get_connection
from database.key_service import mint_room_key, revoke_room_key
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
from utils.components import MetricCard, HotelMapWidget, PhoneCallModal, add_table_filter, monitor_incoming_calls
from utils.logger import log_auth_event

class CashierPage(tk.Frame):
    def __init__(self, parent, current_user: dict, on_logout_cb):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.current_user = current_user
        self.on_logout_cb = on_logout_cb

        self._build_layout()
        self._switch_tab("reservations")
        monitor_incoming_calls(self)

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

        tk.Label(
            title_box,
            text=f"{SYSTEM_NAME.upper()} • FRONT DESK & CASHIER",
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

        user_name = self.current_user.get("name", "Cashier Front Desk")
        img_path = self.current_user.get("image_path", "assets/imgs/employees/f/2.jpg")

        try:
            self.user_avatar = load_image(img_path, (36, 36), circular=True)
            tk.Label(right_hdr, image=self.user_avatar, bg=COLOR_PRIMARY_DARK).pack(side="left", padx=(0, 8))
        except Exception:
            pass

        u_info = tk.Frame(right_hdr, bg=COLOR_PRIMARY_DARK)
        u_info.pack(side="left", padx=(0, 14))

        tk.Label(u_info, text=user_name, font=(FONT_FAMILY, 10, "bold"), fg=COLOR_WHITE, bg=COLOR_PRIMARY_DARK).pack(anchor="e")
        tk.Label(u_info, text="Role: Front Desk Cashier", font=(FONT_FAMILY, 8), fg=COLOR_ACCENT, bg=COLOR_PRIMARY_DARK).pack(anchor="e")

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

        # ------------------ MAIN WORKSPACE (SIDEBAR + CONTENT) ------------------
        workspace = tk.Frame(self, bg=COLOR_BG)
        workspace.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(workspace, bg=COLOR_PRIMARY, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="FRONT DESK CONTROLS",
            font=(FONT_FAMILY, 8, "bold"),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY,
            padx=16,
            pady=12
        ).pack(anchor="w")

        self.nav_buttons = {}
        nav_items = [
            ("reservations", "🛎️ Reservations"),
            ("hotel_map", "🏨 Hotel Floor Map"),
            ("customers", "👤 Customer Directory"),
            ("bulletin", "📢 Employee Bulletin"),
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

        if tab_id == "reservations":
            self._render_reservations_tab()
        elif tab_id == "hotel_map":
            self._render_hotel_map_tab()
        elif tab_id == "customers":
            self._render_customers_tab()
        elif tab_id == "bulletin":
            self._render_bulletin_tab()
        elif tab_id == "inbox":
            self._render_inbox_tab()

    def _handle_logout(self):
        log_auth_event(
            event_type="LOGOUT",
            username=self.current_user.get("username", "Cashier"),
            role="Cashier",
            status="SUCCESS",
            details="Cashier signed out."
        )
        self.on_logout_cb()

    # =========================================================================
    # TAB 1: RESERVATION MANAGEMENT
    # =========================================================================
    def _render_reservations_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Guest Bookings & Reservation Operations", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        tk.Button(
            top_bar,
            text="+ Create New Reservation",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._show_new_reservation_modal
        ).pack(side="right")

        table_card = tk.Frame(self.content_container, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        table_card.pack(fill="both", expand=True)

        # Filters
        filt_row = tk.Frame(table_card, bg=COLOR_WHITE)
        filt_row.pack(fill="x", pady=(0, 8))

        tk.Label(filt_row, text="Filter Status:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side="left")

        stat_var = tk.StringVar(value="All")
        for s_opt in ["All", "Checked In", "Pending", "Checked Out", "Canceled"]:
            tk.Radiobutton(
                filt_row, text=s_opt, variable=stat_var, value=s_opt,
                command=lambda: load_reservations(stat_var.get()),
                indicatoron=0, padx=8, pady=3, bg=COLOR_WHITE, selectcolor=COLOR_PRIMARY_TINT,
                fg=COLOR_PRIMARY, relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER,
                font=(FONT_FAMILY, 8, "bold"), cursor="hand2"
            ).pack(side="left", padx=4)

        cols = ("id", "room", "guest", "phone", "checkin", "checkout", "nights", "total", "status")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=14)

        tree.heading("id", text="Res #")
        tree.heading("room", text="Room")
        tree.heading("guest", text="Customer Name")
        tree.heading("phone", text="Phone")
        tree.heading("checkin", text="Check-In")
        tree.heading("checkout", text="Check-Out")
        tree.heading("nights", text="Nights")
        tree.heading("total", text="Est. Total")
        tree.heading("status", text="Status")

        tree.column("id", width=45, anchor="center")
        tree.column("room", width=70, anchor="center")
        tree.column("guest", width=160, anchor="w")
        tree.column("phone", width=120, anchor="center")
        tree.column("checkin", width=95, anchor="center")
        tree.column("checkout", width=95, anchor="center")
        tree.column("nights", width=60, anchor="center")
        tree.column("total", width=95, anchor="e")
        tree.column("status", width=110, anchor="center")

        tree.tag_configure("in", background=COLOR_SUCCESS_BG, foreground=COLOR_SUCCESS_TEXT)
        tree.tag_configure("pending", background=COLOR_INFO_BG, foreground=COLOR_INFO_TEXT)
        tree.tag_configure("out", background=COLOR_BG, foreground=COLOR_TEXT_MUTED)

        def load_reservations(filter_status="All"):
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                q = """
                    SELECT res.*, r.room_number, r.price_per_night, c.name AS customer_name, c.mobile_number
                    FROM reservations res
                    JOIN rooms r ON res.room_id = r.id
                    JOIN customers c ON res.customer_id = c.id
                    ORDER BY res.id DESC
                """
                rows = conn.execute(q).fetchall()

            for r in rows:
                st = r["status"]
                if filter_status != "All" and st != filter_status:
                    continue

                try:
                    ci = datetime.strptime(r["check_in_date"], "%Y-%m-%d").date()
                    co = datetime.strptime(r["check_out_date"], "%Y-%m-%d").date()
                    nights = max(1, (co - ci).days)
                except Exception:
                    nights = 1

                total_est = nights * r["price_per_night"]

                tag = ()
                if st == "Checked In":
                    tag = ("in",)
                elif st == "Pending":
                    tag = ("pending",)
                elif st == "Checked Out":
                    tag = ("out",)

                tree.insert("", "end", values=(
                    f"#{r['id']}", f"Room {r['room_number']}", r["customer_name"],
                    r["mobile_number"], r["check_in_date"], r["check_out_date"],
                    nights, f"₱{total_est:,.0f}", st
                ), tags=tag)
            if "refresh_reservation_filter" in locals():
                refresh_reservation_filter()

        refresh_reservation_filter = add_table_filter(table_card, tree)
        load_reservations("All")
        tree.pack(fill="both", expand=True)

        # Action Buttons
        act_f = tk.Frame(table_card, bg=COLOR_WHITE)
        act_f.pack(fill="x", pady=(10, 0))

        def check_in_guest():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Reservation", "Please select a pending reservation to check in.")
                return
            res_id_str = tree.item(sel[0])["values"][0].replace("#", "")
            res_id = int(res_id_str)

            with get_connection() as conn:
                res = conn.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
                if not res or res["status"] != "Pending":
                    messagebox.showerror("Error", "Only 'Pending' reservations can be checked in.")
                    return
                # Update reservation to Checked In and room to Occupied
                conn.execute("UPDATE reservations SET status = 'Checked In' WHERE id = ?", (res_id,))
                conn.execute("UPDATE rooms SET status = 'Occupied', is_occupied = 1, is_reserved = 0 WHERE id = ?", (res["room_id"],))
                conn.commit()
                mint_room_key(res["room_id"], res["customer_id"], res_id)

            messagebox.showinfo("Check-In Complete", f"Reservation #{res_id} is now Checked In. Room keycard issued!")
            load_reservations(stat_var.get())
            refresh_reservation_filter()

        tk.Button(
            act_f,
            text="🔑 Check In Guest",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=check_in_guest
        ).pack(side="left", padx=4)

        def check_out_guest():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Reservation", "Please select an active Checked-In reservation to check out.")
                return
            res_id_str = tree.item(sel[0])["values"][0].replace("#", "")
            res_id = int(res_id_str)

            with get_connection() as conn:
                res = conn.execute("""
                    SELECT res.*, r.price_per_night, r.room_number, c.name AS cust_name, c.loyalty_points
                    FROM reservations res
                    JOIN rooms r ON res.room_id = r.id
                    JOIN customers c ON res.customer_id = c.id
                    WHERE res.id = ?
                """, (res_id,)).fetchone()

                if not res or res["status"] != "Checked In":
                    messagebox.showerror("Error", "Only currently 'Checked In' guests can be checked out.")
                    return

                try:
                    ci = datetime.strptime(res["check_in_date"], "%Y-%m-%d").date()
                    co = datetime.strptime(res["check_out_date"], "%Y-%m-%d").date()
                    nights = max(1, (co - ci).days)
                except Exception:
                    nights = 1

                bill_amt = nights * res["price_per_night"]
                pts_earned = int(bill_amt // 100)

                # Prompt Cashier for billing confirmation
                confirm_msg = (
                    f"FINAL BILL SETTLEMENT FOR {res['cust_name'].upper()}\n\n"
                    f"Room: {res['room_number']} ({nights} night(s))\n"
                    f"Total Room Billing: PHP {bill_amt:,.2f}\n"
                    f"Loyalty Points Awarded: +{pts_earned} pts\n\n"
                    f"Confirm payment receipt and proceed with Check-Out?"
                )
                if not messagebox.askyesno("Confirm Check-Out & Settlement", confirm_msg):
                    return

                # Record Revenue Transaction
                conn.execute("""
                    INSERT INTO transactions (type, amount, description, customer_id, date_recorded)
                    VALUES ('Revenue', ?, ?, ?, CURRENT_TIMESTAMP)
                """, (bill_amt, f"Room #{res['room_number']} Checkout - {nights} nights ({res['cust_name']})", res["customer_id"]))

                # Update Loyalty Points
                conn.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE id = ?", (pts_earned, res["customer_id"]))

                # Mark reservation Checked Out
                conn.execute("UPDATE reservations SET status = 'Checked Out' WHERE id = ?", (res_id,))

                # Mark Room as 'Needs Service' so Utilities Housekeeping is dispatched!
                conn.execute("UPDATE rooms SET status = 'Needs Service', is_occupied = 0, is_reserved = 0 WHERE id = ?", (res["room_id"],))

                # Add automated room service cleanup task in service_requests
                conn.execute("""
                    INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
                    VALUES (?, ?, 'Room Service', 'Post checkout full-swing sanitation and linen replacement.', 'Processing')
                """, (res["room_id"], res["customer_id"]))

                conn.commit()
                revoke_room_key(res["room_id"], res_id)

            messagebox.showinfo("Checkout Complete", f"Guest checked out successfully!\nRoom {res['room_number']} marked for housekeeping service.")
            load_reservations(stat_var.get())

        tk.Button(
            act_f,
            text="💳 Settle & Check Out Guest",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=check_out_guest
        ).pack(side="left", padx=4)

        def change_room():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Reservation", "Please select a pending or checked-in reservation.")
                return

            res_id = int(tree.item(sel[0])["values"][0].replace("#", ""))
            with get_connection() as conn:
                reservation = conn.execute("""
                    SELECT res.*, r.room_number AS current_room_number, c.name AS guest_name
                    FROM reservations res
                    JOIN rooms r ON res.room_id = r.id
                    JOIN customers c ON res.customer_id = c.id
                    WHERE res.id = ?
                """, (res_id,)).fetchone()
                available_rooms = conn.execute("""
                    SELECT id, room_number, type, price_per_night
                    FROM rooms
                    WHERE status = 'Vacant' AND id != ?
                    ORDER BY room_number ASC
                """, (reservation["room_id"],)).fetchall() if reservation else []

            if not reservation or reservation["status"] not in ("Pending", "Checked In"):
                messagebox.showerror("Room Change Unavailable", "Only pending or checked-in reservations can change rooms.")
                return
            if not available_rooms:
                messagebox.showwarning("No Rooms Available", "There are no vacant rooms available for this guest.")
                return

            modal = tk.Toplevel(self)
            modal.title("Change Guest Room")
            modal.geometry("440x240")
            modal.configure(bg=COLOR_WHITE)
            modal.transient(self)
            modal.grab_set()

            tk.Label(
                modal,
                text=f"CHANGE ROOM FOR {reservation['guest_name'].upper()}",
                font=(FONT_FAMILY, 11, "bold"),
                fg=COLOR_PRIMARY,
                bg=COLOR_WHITE
            ).pack(pady=(14, 4))
            tk.Label(
                modal,
                text=f"Current room: Room {reservation['current_room_number']}",
                font=(FONT_FAMILY, 9),
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_WHITE
            ).pack(pady=(0, 10))

            form = tk.Frame(modal, bg=COLOR_WHITE, padx=24)
            form.pack(fill="x")
            tk.Label(
                form, text="Select New Available Room:",
                font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE
            ).pack(anchor="w")
            room_map = {
                f"Room {room['room_number']} - {room['type']} (₱{room['price_per_night']:,.0f}/night)": room["id"]
                for room in available_rooms
            }
            room_var = tk.StringVar(value=next(iter(room_map)))
            room_cb = ttk.Combobox(
                form, textvariable=room_var, values=list(room_map), state="readonly"
            )
            room_cb.pack(fill="x", pady=(3, 12))

            def apply_room_change():
                new_room_id = room_map.get(room_var.get())
                if not new_room_id:
                    messagebox.showwarning("Select Room", "Please select a new room.")
                    return
                if not messagebox.askyesno(
                    "Confirm Room Change",
                    f"Move {reservation['guest_name']} from Room {reservation['current_room_number']} "
                    f"to {room_var.get().split(' - ', 1)[0]}?"
                ):
                    return

                with get_connection() as conn:
                    current = conn.execute(
                        "SELECT status, room_id FROM reservations WHERE id = ?", (res_id,)
                    ).fetchone()
                    new_room = conn.execute(
                        "SELECT room_number, status FROM rooms WHERE id = ?", (new_room_id,)
                    ).fetchone()
                    if not current or current["status"] not in ("Pending", "Checked In"):
                        messagebox.showerror("Room Change Unavailable", "This reservation is no longer eligible for a room change.")
                        return
                    if not new_room or new_room["status"] != "Vacant":
                        messagebox.showerror("Room Unavailable", "The selected room is no longer vacant.")
                        return

                    old_room_status = "Vacant" if current["status"] == "Pending" else "Needs Service"
                    conn.execute(
                        "UPDATE rooms SET status = ?, is_reserved = 0, is_occupied = 0 WHERE id = ?",
                        (old_room_status, current["room_id"])
                    )
                    if current["status"] == "Pending":
                        conn.execute(
                            "UPDATE rooms SET status = 'Reserved', is_reserved = 1, is_occupied = 0 WHERE id = ?",
                            (new_room_id,)
                        )
                    else:
                        conn.execute(
                            "UPDATE rooms SET status = 'Occupied', is_reserved = 0, is_occupied = 1 WHERE id = ?",
                            (new_room_id,)
                        )
                        conn.execute("""
                            INSERT INTO service_requests (room_id, customer_id, request_type, details, status)
                            VALUES (?, ?, 'Room Service', 'Room change sanitation and inspection.', 'Processing')
                        """, (current["room_id"], reservation["customer_id"]))
                    conn.execute(
                        "UPDATE reservations SET room_id = ? WHERE id = ?",
                        (new_room_id, res_id)
                    )
                    conn.commit()

                modal.destroy()
                messagebox.showinfo("Room Changed", f"Guest moved to Room {new_room['room_number']}.")
                load_reservations(stat_var.get())

            tk.Button(
                modal,
                text="Confirm Room Change",
                font=(FONT_FAMILY, 10, "bold"),
                bg=COLOR_PRIMARY,
                fg=COLOR_WHITE,
                relief="flat",
                padx=14,
                pady=6,
                command=apply_room_change
            ).pack(pady=6)

        tk.Button(
            act_f,
            text="🔄 Change Room",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=change_room
        ).pack(side="left", padx=4)

        def cancel_reservation():
            sel = tree.selection()
            if not sel:
                return
            res_id_str = tree.item(sel[0])["values"][0].replace("#", "")
            res_id = int(res_id_str)

            if messagebox.askyesno("Cancel Booking", f"Are you sure you want to cancel reservation #{res_id}?"):
                with get_connection() as conn:
                    res = conn.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
                    if res:
                        conn.execute("UPDATE reservations SET status = 'Canceled' WHERE id = ?", (res_id,))
                        conn.execute("UPDATE rooms SET status = 'Vacant', is_reserved = 0, is_occupied = 0 WHERE id = ?", (res["room_id"],))
                        conn.commit()
                load_reservations(stat_var.get())

        tk.Button(
            act_f,
            text="Cancel Booking",
            font=(FONT_FAMILY, 9),
            bg=COLOR_BG,
            fg=COLOR_DANGER,
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=cancel_reservation
        ).pack(side="left", padx=4)

    def _show_new_reservation_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Create New Reservation")
        modal.geometry("450x460")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="NEW GUEST RESERVATION", font=(FONT_FAMILY, 12, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25)
        form.pack(fill="both", expand=True)

        with get_connection() as conn:
            customers = conn.execute("SELECT id, name, mobile_number FROM customers ORDER BY name ASC").fetchall()
            vacant_rooms = conn.execute("SELECT id, room_number, type, price_per_night FROM rooms WHERE status = 'Vacant' ORDER BY room_number ASC").fetchall()

        if not vacant_rooms:
            messagebox.showwarning("No Rooms Available", "All rooms are currently occupied or reserved.")
            modal.destroy()
            return

        # Customer selection
        tk.Label(form, text="Select Guest:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        cust_map = {f"{c['name']} ({c['mobile_number']})": c["id"] for c in customers}
        cust_var = tk.StringVar(value=list(cust_map.keys())[0] if cust_map else "")
        cust_cb = ttk.Combobox(form, textvariable=cust_var, values=list(cust_map.keys()), state="readonly")
        cust_cb.pack(fill="x", pady=(2, 10))

        # Room selection
        tk.Label(form, text="Select Available Room:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        room_map = {f"Room {r['room_number']} - {r['type']} (₱{r['price_per_night']:,.0f}/night)": r["id"] for r in vacant_rooms}
        room_var = tk.StringVar(value=list(room_map.keys())[0] if room_map else "")
        room_cb = ttk.Combobox(form, textvariable=room_var, values=list(room_map.keys()), state="readonly")
        room_cb.pack(fill="x", pady=(2, 10))

        # Check in and out dates
        today_str = date.today().strftime("%Y-%m-%d")
        checkout_default = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")

        tk.Label(form, text="Check-In Date (YYYY-MM-DD):", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        ci_entry = tk.Entry(form, font=(FONT_FAMILY, 10), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        ci_entry.pack(fill="x", ipady=3, pady=(2, 10))
        ci_entry.insert(0, today_str)

        tk.Label(form, text="Check-Out Date (YYYY-MM-DD):", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        co_entry = tk.Entry(form, font=(FONT_FAMILY, 10), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        co_entry.pack(fill="x", ipady=3, pady=(2, 12))
        co_entry.insert(0, checkout_default)

        def save_booking():
            c_name = cust_var.get()
            r_str = room_var.get()
            ci = ci_entry.get().strip()
            co = co_entry.get().strip()

            if not c_name or not r_str or not ci or not co:
                messagebox.showwarning("Missing Info", "All fields are required.")
                return

            cust_id = cust_map[c_name]
            room_id = room_map[r_str]

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO reservations (customer_id, room_id, check_in_date, check_out_date, status)
                    VALUES (?, ?, ?, ?, 'Pending')
                """, (cust_id, room_id, ci, co))
                conn.execute("UPDATE rooms SET status = 'Reserved', is_reserved = 1 WHERE id = ?", (room_id,))
                conn.commit()

            messagebox.showinfo("Success", f"Reservation created for {c_name}!\nRoom marked as Reserved.")
            modal.destroy()
            self._switch_tab("reservations")

        tk.Button(modal, text="Confirm & Save Reservation", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=16, pady=7, command=save_booking).pack(pady=10)

    # =========================================================================
    # TAB 2: HOTEL MAP
    # =========================================================================
    def _render_hotel_map_tab(self):
        hotel_map = HotelMapWidget(self.content_container, get_connection, utilities_mode=False)
        hotel_map.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 3: CUSTOMER DIRECTORY
    # =========================================================================
    def _render_customers_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Registered Guest Database & Profiles", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        table_card = tk.Frame(self.content_container, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        table_card.pack(fill="both", expand=True)

        cols = ("id", "name", "email", "phone", "pts", "stay")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=14)

        tree.heading("id", text="ID")
        tree.heading("name", text="Guest Name")
        tree.heading("email", text="Email")
        tree.heading("phone", text="Phone Number")
        tree.heading("pts", text="Loyalty Points")
        tree.heading("stay", text="Active Stay")

        tree.column("id", width=40, anchor="center")
        tree.column("name", width=170, anchor="w")
        tree.column("email", width=200, anchor="w")
        tree.column("phone", width=130, anchor="center")
        tree.column("pts", width=110, anchor="e")
        tree.column("stay", width=140, anchor="center")

        def load_c():
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                q = """
                    SELECT c.*, r.room_number
                    FROM customers c
                    LEFT JOIN reservations res ON c.id = res.customer_id AND res.status = 'Checked In'
                    LEFT JOIN rooms r ON res.room_id = r.id
                    ORDER BY c.id ASC
                """
                custs = conn.execute(q).fetchall()

            for c in custs:
                stay_txt = f"Room {c['room_number']}" if c["room_number"] else "Not Checked In"
                tree.insert("", "end", values=(
                    c["id"], c["name"], c["email"] or "N/A", c["mobile_number"] or "N/A",
                    f"{c['loyalty_points'] or 0} pts", stay_txt
                ))

        refresh_customer_filter = add_table_filter(table_card, tree)
        load_c()
        refresh_customer_filter()
        tree.pack(fill="both", expand=True)

        # Call Guest button
        act_f = tk.Frame(table_card, bg=COLOR_WHITE)
        act_f.pack(fill="x", pady=(10, 0))

        def call_guest():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Guest", "Please select a guest from the table.")
                return
            c_id = tree.item(sel[0])["values"][0]
            with get_connection() as conn:
                guest = conn.execute("SELECT * FROM customers WHERE id = ?", (c_id,)).fetchone()
            if guest:
                PhoneCallModal(self, guest["name"], guest["mobile_number"], "Registered Guest", guest["image_path"])

        tk.Button(
            act_f,
            text="📞 Call Guest",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=call_guest
        ).pack(side="left")

    # =========================================================================
    # TAB 4: BULLETIN
    # =========================================================================
    def _render_bulletin_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Employee Bulletin & Official Hotel Notices", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

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

        directory_search = tk.StringVar()
        tk.Label(left_card, text="Search staff:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")
        tk.Entry(left_card, textvariable=directory_search, font=FONT_SMALL, relief="solid", bd=1).pack(fill="x", pady=(2, 8), ipady=4)

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
                command=lambda name=s_dict["name"], ph=s_dict["phone"], role=s_dict["role"], img=s_dict["image_path"], uid=s_dict["id"], staff=s_dict, rw=row_box: (
                    highlight_staff(staff, rw),
                    PhoneCallModal(self, name, ph, role, img, uid)
                )
            )
            call_btn.pack(side="right", padx=6)

            if idx == 0:
                highlight_staff(s_dict, row_box)

        def filter_directory(*_):
            query = directory_search.get().strip().casefold()
            for row_box in selected_user_state["row_widgets"]:
                row_text = " ".join(
                    str(widget.cget("text")) for widget in row_box.winfo_children()
                    if isinstance(widget, tk.Label)
                ).casefold()
                nested_text = " ".join(
                    str(child.cget("text"))
                    for child in row_box.winfo_children()
                    for child in (child.winfo_children() if isinstance(child, tk.Frame) else [])
                    if isinstance(child, tk.Label)
                ).casefold()
                if query in f"{row_text} {nested_text}":
                    row_box.pack(fill="x", pady=2)
                else:
                    row_box.pack_forget()

        directory_search.trace_add("write", filter_directory)

        # Right: Dispatch message composer and feed
        right_card = tk.Frame(panes, bg=COLOR_WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(right_card, text="INTER-DEPARTMENT DISPATCH", font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 6))

        tk.Button(
            right_card,
            text="+ Dispatch Message to Staff",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._show_dispatch_modal
        ).pack(anchor="w", pady=(0, 10))

        message_search = tk.StringVar()
        tk.Label(
            right_card, text="Search messages:", font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE
        ).pack(anchor="w")
        tk.Entry(
            right_card, textvariable=message_search, font=FONT_SMALL,
            relief="solid", bd=1
        ).pack(fill="x", pady=(0, 8), ipady=4)
        message_cards = []

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

            target_tag = f"Target: {m['receiver_role'] or 'Direct User'}"
            tk.Label(top, text=f"{m['sender_name']} ({m['sender_role']})", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(side="left")
            tk.Label(top, text=target_tag, font=(FONT_FAMILY, 8, "bold"), fg=COLOR_ACCENT, bg=COLOR_WHITE).pack(side="left", padx=8)
            tk.Label(top, text=str(m["timestamp"])[:16], font=(FONT_FAMILY, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side="right")

            tk.Label(m_card, text=m["content"], font=(FONT_FAMILY, 9), fg=COLOR_TEXT_NORMAL, bg=COLOR_WHITE, wraplength=400, justify="left").pack(anchor="w", pady=(3, 0))
            message_cards.append((m_card, " ".join(str(value or "") for value in (
                m["sender_name"], m["sender_role"], m["receiver_role"], m["content"], m["timestamp"]
            )).casefold()))

        def filter_messages(*_):
            query = message_search.get().strip().casefold()
            for card, text in message_cards:
                if query in text:
                    card.pack(fill="x", pady=3)
                else:
                    card.pack_forget()

        message_search.trace_add("write", filter_messages)

    def _show_dispatch_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Dispatch Message")
        modal.geometry("400x340")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="FRONT DESK DISPATCH", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Send To Target Role:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        role_var = tk.StringVar(value="Staff_Utilities")
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

        tk.Button(modal, text="Send Dispatch", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=14, pady=5, command=send).pack(pady=10)
