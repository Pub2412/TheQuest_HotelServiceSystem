"""
Admin Portal for The Quest Hotel Management System.
Features:
- Total Revenue, Running Costs (Utilities & Goods), Total Guests with custom Canvas charts
- PDF Audit Report Generation
- Interactive Hotel Floor Map Room visualizer
- Active Customer Stays & Live Overdue/Near-Overdue Alert System
- Utility Inventory & Goods Restock Management
- User (Admin, Cashier, Staff) management with Profile Images
- Customer (RUD) & Loyalty Points Management
- Loyalty Rewards / Promotional Attainments management
- Employee Bulletin Announcements
- Employee Inbox & Interactive Voice Softphone Calling
- Decrypted Login/Logout Authentication & System Health Audit Logs
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import sqlite3
import os
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
from utils.components import MetricCard, HotelMapWidget, PhoneCallModal, add_table_filter, monitor_incoming_calls
from utils.pdf_exporter import generate_hotel_pdf_report
from utils.logger import read_decrypted_auth_logs, read_system_health_logs, log_auth_event

class AdminPage(tk.Frame):
    def __init__(self, parent, current_user: dict, on_logout_cb):
        super().__init__(parent, bg=COLOR_BG)
        self.parent = parent
        self.current_user = current_user
        self.on_logout_cb = on_logout_cb

        self._active_tab_btn = None
        self._build_layout()
        self._switch_tab("analytics")
        monitor_incoming_calls(self)

    def _build_layout(self):
        # ------------------ TOP APP HEADER ------------------
        header = tk.Frame(self, bg=COLOR_PRIMARY_DARK, height=64)
        header.pack(fill="x", side="top")

        left_hdr = tk.Frame(header, bg=COLOR_PRIMARY_DARK)
        left_hdr.pack(side="left", padx=16, pady=8)

        # Brand Icon & Title
        try:
            self.icon_photo = get_icon_logo((36, 36))
            tk.Label(left_hdr, image=self.icon_photo, bg=COLOR_PRIMARY_DARK).pack(side="left", padx=(0, 10))
        except Exception:
            pass

        title_box = tk.Frame(left_hdr, bg=COLOR_PRIMARY_DARK)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text=f"{SYSTEM_NAME.upper()} • ADMIN CONSOLE",
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

        # Right Header (User Profile + Logout)
        right_hdr = tk.Frame(header, bg=COLOR_PRIMARY_DARK)
        right_hdr.pack(side="right", padx=16, pady=8)

        user_name = self.current_user.get("name", "Administrator")
        user_role = self.current_user.get("role", "Admin")

        # User photo avatar
        img_path = self.current_user.get("image_path", "assets/imgs/employees/f/1.jpg")
        try:
            self.user_avatar = load_image(img_path, (36, 36), circular=True)
            tk.Label(right_hdr, image=self.user_avatar, bg=COLOR_PRIMARY_DARK).pack(side="left", padx=(0, 8))
        except Exception:
            pass

        u_info = tk.Frame(right_hdr, bg=COLOR_PRIMARY_DARK)
        u_info.pack(side="left", padx=(0, 14))

        tk.Label(u_info, text=user_name, font=(FONT_FAMILY, 10, "bold"), fg=COLOR_WHITE, bg=COLOR_PRIMARY_DARK).pack(anchor="e")
        tk.Label(u_info, text=f"Clearance: {user_role}", font=(FONT_FAMILY, 8), fg=COLOR_ACCENT, bg=COLOR_PRIMARY_DARK).pack(anchor="e")

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

        # Sidebar Navigation
        self.sidebar = tk.Frame(workspace, bg=COLOR_PRIMARY, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="NAVIGATION",
            font=(FONT_FAMILY, 8, "bold"),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY,
            padx=16,
            pady=12
        ).pack(anchor="w")

        self.nav_buttons = {}
        nav_items = [
            ("analytics", "📊 Executive Analytics"),
            ("hotel_map", "🏨 Hotel Floor Map"),
            ("stays", "🛎️ Active Stays & Alerts"),
            ("inventory", "📦 Inventory & Restock"),
            ("users", "👥 Staff Management"),
            ("customers", "🌟 Guest Database"),
            ("rewards", "🎁 Loyalty Rewards"),
            ("bulletin", "📢 Staff Bulletin"),
            ("inbox", "💬 Inbox & Voice Call"),
            ("logs", "🔒 Security & Health Logs"),
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
                pady=9,
                relief="flat",
                cursor="hand2",
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(fill="x")
            self.nav_buttons[tab_id] = btn

        # Content Area
        self.content_container = tk.Frame(workspace, bg=COLOR_BG, padx=16, pady=16)
        self.content_container.pack(side="right", fill="both", expand=True)

    def _switch_tab(self, tab_id: str):
        # Update sidebar active state
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.config(bg=COLOR_PRIMARY_LIGHT, fg=COLOR_ACCENT)
            else:
                btn.config(bg=COLOR_PRIMARY, fg=COLOR_WHITE)

        # Clear content container
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Render selected tab
        if tab_id == "analytics":
            self._render_analytics_tab()
        elif tab_id == "hotel_map":
            self._render_hotel_map_tab()
        elif tab_id == "stays":
            self._render_stays_tab()
        elif tab_id == "inventory":
            self._render_inventory_tab()
        elif tab_id == "users":
            self._render_users_tab()
        elif tab_id == "customers":
            self._render_customers_tab()
        elif tab_id == "rewards":
            self._render_rewards_tab()
        elif tab_id == "bulletin":
            self._render_bulletin_tab()
        elif tab_id == "inbox":
            self._render_inbox_tab()
        elif tab_id == "logs":
            self._render_logs_tab()

    def _handle_logout(self):
        log_auth_event(
            event_type="LOGOUT",
            username=self.current_user.get("username", "Admin"),
            role="Admin",
            status="SUCCESS",
            details="Admin logged out gracefully."
        )
        self.on_logout_cb()

    # =========================================================================
    # TAB 1: EXECUTIVE ANALYTICS & PDF AUDIT REPORT
    # =========================================================================
    def _render_analytics_tab(self):
        # Top Action Bar
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 12))

        tk.Label(
            top_bar,
            text="Executive Financial & Operational Analytics",
            font=FONT_HEADING,
            fg=COLOR_PRIMARY,
            bg=COLOR_BG
        ).pack(side="left")

        pdf_btn = tk.Button(
            top_bar,
            text="📄 Generate PDF Audit Report",
            font=(FONT_FAMILY, 10, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            activebackground=COLOR_ACCENT_HOVER,
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._export_pdf_report
        )
        pdf_btn.pack(side="right")

        # Fetch Financial & Room metrics
        with get_connection() as conn:
            # Revenue
            rev_row = conn.execute("SELECT SUM(amount) AS total FROM transactions WHERE type = 'Revenue'").fetchone()
            total_revenue = rev_row["total"] or 0.0

            # Costs Breakdown
            cost_util_row = conn.execute("SELECT SUM(amount) AS total FROM transactions WHERE type = 'Cost_Utility'").fetchone()
            cost_utility = cost_util_row["total"] or 0.0

            cost_goods_row = conn.execute("SELECT SUM(amount) AS total FROM transactions WHERE type = 'Cost_Goods'").fetchone()
            cost_goods = cost_goods_row["total"] or 0.0

            total_costs = cost_utility + cost_goods
            net_profit = total_revenue - total_costs

            # Guests count
            guest_count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

            # Rooms stats
            rooms_total = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            rooms_occ = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'").fetchone()[0]
            rooms_svc = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Needs Service'").fetchone()[0]
            rooms_res = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Reserved'").fetchone()[0]
            rooms_vac = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Vacant'").fetchone()[0]

            occupancy_pct = (rooms_occ / rooms_total * 100) if rooms_total > 0 else 0

        # KPI Metrics Row
        kpi_frame = tk.Frame(self.content_container, bg=COLOR_BG)
        kpi_frame.pack(fill="x", pady=(0, 16))

        for c in range(4):
            kpi_frame.columnconfigure(c, weight=1)

        c1 = MetricCard(kpi_frame, "Total Revenue", f"PHP {total_revenue:,.0f}", f"Net Profit: PHP {net_profit:,.0f}", badge="Income")
        c1.grid(row=0, column=0, padx=6, sticky="nsew")

        c2 = MetricCard(kpi_frame, "Total Running Costs", f"PHP {total_costs:,.0f}", f"Util: ₱{cost_utility:,.0f} | Goods: ₱{cost_goods:,.0f}", badge="Expenses")
        c2.grid(row=0, column=1, padx=6, sticky="nsew")

        c3 = MetricCard(kpi_frame, "Hotel Occupancy", f"{occupancy_pct:.1f}%", f"{rooms_occ} of {rooms_total} rooms occupied", badge=f"{rooms_occ} Occ")
        c3.grid(row=0, column=2, padx=6, sticky="nsew")

        c4 = MetricCard(kpi_frame, "Registered Guests", f"{guest_count}", "Loyalty Database Active", badge="Guests")
        c4.grid(row=0, column=3, padx=6, sticky="nsew")

        # Two Graphs Side-by-Side (Canvas-based)
        charts_frame = tk.Frame(self.content_container, bg=COLOR_BG)
        charts_frame.pack(fill="both", expand=True)
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)

        # Graph 1: Revenue vs Costs Bar Chart
        g1_card = tk.Frame(charts_frame, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        g1_card.grid(row=0, column=0, padx=6, sticky="nsew")

        tk.Label(g1_card, text="Financial Breakdown: Revenue vs Operational Costs", font=FONT_TITLE, fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w")

        c_bar = tk.Canvas(g1_card, bg=COLOR_WHITE, height=220, highlightthickness=0)
        c_bar.pack(fill="both", expand=True, pady=10)

        self._draw_bar_chart(c_bar, [
            ("Revenue", total_revenue, COLOR_SUCCESS),
            ("Utilities", cost_utility, COLOR_INFO),
            ("Goods Restock", cost_goods, COLOR_WARNING),
            ("Net Profit", max(0, net_profit), COLOR_PRIMARY)
        ])

        # Graph 2: Room Status Allocation Donut Chart
        g2_card = tk.Frame(charts_frame, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        g2_card.grid(row=0, column=1, padx=6, sticky="nsew")

        tk.Label(g2_card, text="Room Capacity & Operational Allocation", font=FONT_TITLE, fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w")

        c_donut = tk.Canvas(g2_card, bg=COLOR_WHITE, height=220, highlightthickness=0)
        c_donut.pack(fill="both", expand=True, pady=10)

        self._draw_room_status_chart(c_donut, [
            ("Occupied", rooms_occ, COLOR_DANGER),
            ("Vacant", rooms_vac, COLOR_SUCCESS),
            ("Needs Service", rooms_svc, COLOR_WARNING),
            ("Reserved", rooms_res, COLOR_INFO),
        ], rooms_total)

    def _draw_bar_chart(self, canvas, data):
        canvas.update_idletasks()
        w = canvas.winfo_width() or 420
        h = canvas.winfo_height() or 200

        max_val = max([val for _, val, _ in data] + [1])
        margin_b = 30
        margin_t = 20
        avail_h = h - margin_b - margin_t
        n = len(data)
        bar_w = min(60, int((w - 40) / (n * 1.6)))
        gap = int((w - 40 - (n * bar_w)) / (n + 1))

        # Baseline
        canvas.create_line(20, h - margin_b, w - 20, h - margin_b, fill=COLOR_BORDER, width=2)

        for i, (label, val, col) in enumerate(data):
            bar_h = int((val / max_val) * (avail_h - 20))
            x0 = 20 + gap + i * (bar_w + gap)
            y0 = (h - margin_b) - bar_h
            x1 = x0 + bar_w
            y1 = h - margin_b

            # Bar
            canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="", width=0)
            # Value label
            canvas.create_text((x0 + x1) / 2, y0 - 8, text=f"₱{val/1000:,.1f}k", font=(FONT_FAMILY, 8, "bold"), fill=COLOR_TEXT_NORMAL)
            # Category label
            canvas.create_text((x0 + x1) / 2, h - margin_b + 12, text=label, font=(FONT_FAMILY, 8), fill=COLOR_TEXT_MUTED)

    def _draw_room_status_chart(self, canvas, data, total_rooms):
        canvas.update_idletasks()
        w = canvas.winfo_width() or 420
        h = canvas.winfo_height() or 200

        cx = 120
        cy = h // 2
        r = 65

        start_ang = 0
        for label, count, col in data:
            if total_rooms > 0 and count > 0:
                extent = (count / total_rooms) * 360
                canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=start_ang, extent=extent, fill=col, outline=COLOR_WHITE, width=2)
                start_ang += extent

        # Center cutout for donut effect
        r_inner = 35
        canvas.create_oval(cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner, fill=COLOR_WHITE, outline="")
        canvas.create_text(cx, cy - 6, text=f"{total_rooms}", font=(FONT_FAMILY, 14, "bold"), fill=COLOR_PRIMARY)
        canvas.create_text(cx, cy + 10, text="ROOMS", font=(FONT_FAMILY, 7, "bold"), fill=COLOR_TEXT_MUTED)

        # Legend on right side
        lx = 220
        ly = cy - 40
        for label, count, col in data:
            pct = (count / total_rooms * 100) if total_rooms > 0 else 0
            canvas.create_rectangle(lx, ly, lx + 12, ly + 12, fill=col, outline="")
            canvas.create_text(lx + 20, ly + 6, text=f"{label}: {count} ({pct:.0f}%)", anchor="w", font=(FONT_FAMILY, 9), fill=COLOR_TEXT_DARK)
            ly += 22

    def _export_pdf_report(self):
        """Generates comprehensive PDF audit report using fpdf."""
        filepath = filedialog.asksaveasfilename(
            title="Save Hotel Management PDF Report",
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile=f"TheQuest_Executive_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        )
        if not filepath:
            return

        try:
            with get_connection() as conn:
                rev = conn.execute("SELECT SUM(amount) AS total FROM transactions WHERE type = 'Revenue'").fetchone()["total"] or 0.0
                cost_u = conn.execute("SELECT SUM(amount) AS total FROM transactions WHERE type = 'Cost_Utility'").fetchone()["total"] or 0.0
                cost_g = conn.execute("SELECT SUM(amount) AS total FROM transactions WHERE type = 'Cost_Goods'").fetchone()["total"] or 0.0
                guests = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

                r_tot = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
                r_occ = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'").fetchone()[0]
                r_res = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Reserved'").fetchone()[0]
                r_vac = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Vacant'").fetchone()[0]
                r_svc = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Needs Service'").fetchone()[0]

                tx_rows = [dict(r) for r in conn.execute("SELECT * FROM transactions ORDER BY date_recorded DESC LIMIT 30").fetchall()]

            metrics = {
                "revenue": rev,
                "costs": cost_u + cost_g,
                "cost_utility": cost_u,
                "cost_goods": cost_g,
                "guests": guests
            }
            room_stats = {
                "total": r_tot,
                "occupied": r_occ,
                "reserved": r_res,
                "vacant": r_vac,
                "needs_service": r_svc,
                "occupancy_pct": (r_occ / r_tot * 100) if r_tot > 0 else 0
            }

            admin_name = self.current_user.get("name", "Executive Administrator")
            generate_hotel_pdf_report(filepath, metrics, tx_rows, room_stats, admin_name)

            messagebox.showinfo(
                "PDF Export Successful",
                f"Executive Audit Report successfully generated at:\n{filepath}"
            )
        except Exception as err:
            messagebox.showerror("Export Failed", f"Could not create PDF report:\n{err}")

    # =========================================================================
    # TAB 2: HOTEL MAP VISUALIZER
    # =========================================================================
    def _render_hotel_map_tab(self):
        hotel_map = HotelMapWidget(self.content_container, get_connection, utilities_mode=False)
        hotel_map.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 3: ACTIVE STAYS & OVERDUE ALERTS
    # =========================================================================
    def _render_stays_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(
            top_bar,
            text="Guest Stay Duration & Overdue Status Monitor",
            font=FONT_HEADING,
            fg=COLOR_PRIMARY,
            bg=COLOR_BG
        ).pack(side="left")

        # Query active stays
        today_str = date.today().strftime("%Y-%m-%d")
        with get_connection() as conn:
            query = """
                SELECT res.id AS res_id, res.check_in_date, res.check_out_date, res.status,
                       r.room_number, r.type AS room_type, r.price_per_night,
                       c.id AS customer_id, c.name AS customer_name, c.mobile_number, c.loyalty_points
                FROM reservations res
                JOIN rooms r ON res.room_id = r.id
                JOIN customers c ON res.customer_id = c.id
                WHERE res.status = 'Checked In'
                ORDER BY res.check_out_date ASC
            """
            stays = conn.execute(query).fetchall()

        overdue_stays = []
        near_overdue_stays = []
        normal_stays = []

        for s in stays:
            co = str(s["check_out_date"])
            if co < today_str:
                overdue_stays.append(s)
            elif co == today_str:
                near_overdue_stays.append(s)
            else:
                normal_stays.append(s)

        # Prominent Overdue Alert Banner if any
        if overdue_stays or near_overdue_stays:
            alert_card = tk.Frame(self.content_container, bg=COLOR_DANGER_BG, highlightthickness=2, highlightbackground=COLOR_DANGER, padx=14, pady=10)
            alert_card.pack(fill="x", pady=(0, 14))

            tk.Label(
                alert_card,
                text=f"🚨 SECURITY & BILLING ALERT: {len(overdue_stays)} Overdue Guest(s) and {len(near_overdue_stays)} Approaching Checkout Today!",
                font=(FONT_FAMILY, 11, "bold"),
                fg=COLOR_DANGER_TEXT,
                bg=COLOR_DANGER_BG
            ).pack(anchor="w")

            alert_desc = "Front desk and security should notify the guests below for stay extension or immediate checkout clearance."
            tk.Label(alert_card, text=alert_desc, font=(FONT_FAMILY, 9), fg=COLOR_DANGER_TEXT, bg=COLOR_DANGER_BG).pack(anchor="w", pady=(2, 0))

        # Stays Table
        table_card = tk.Frame(self.content_container, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        table_card.pack(fill="both", expand=True)

        cols = ("room", "guest", "phone", "checkin", "checkout", "days", "rate", "status")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=14)

        tree.heading("room", text="Room")
        tree.heading("guest", text="Guest Name")
        tree.heading("phone", text="Phone Number")
        tree.heading("checkin", text="Check-In")
        tree.heading("checkout", text="Check-Out")
        tree.heading("days", text="Duration")
        tree.heading("rate", text="Rate/Night")
        tree.heading("status", text="Stay Status")

        tree.column("room", width=70, anchor="center")
        tree.column("guest", width=160, anchor="w")
        tree.column("phone", width=120, anchor="center")
        tree.column("checkin", width=100, anchor="center")
        tree.column("checkout", width=100, anchor="center")
        tree.column("days", width=90, anchor="center")
        tree.column("rate", width=100, anchor="e")
        tree.column("status", width=140, anchor="center")

        tree.tag_configure("overdue", background=COLOR_DANGER_BG, foreground=COLOR_DANGER_TEXT)
        tree.tag_configure("near_overdue", background=COLOR_WARNING_BG, foreground=COLOR_WARNING_TEXT)

        for s in overdue_stays:
            ci = datetime.strptime(s["check_in_date"], "%Y-%m-%d").date()
            co = datetime.strptime(s["check_out_date"], "%Y-%m-%d").date()
            dur = f"{(co - ci).days} nights"
            tree.insert("", "end", values=(
                f"Room {s['room_number']}", s["customer_name"], s["mobile_number"],
                s["check_in_date"], s["check_out_date"], dur, f"₱{s['price_per_night']:,.0f}",
                "🚨 OVERDUE"
            ), tags=("overdue",))

        for s in near_overdue_stays:
            ci = datetime.strptime(s["check_in_date"], "%Y-%m-%d").date()
            co = datetime.strptime(s["check_out_date"], "%Y-%m-%d").date()
            dur = f"{(co - ci).days} nights"
            tree.insert("", "end", values=(
                f"Room {s['room_number']}", s["customer_name"], s["mobile_number"],
                s["check_in_date"], s["check_out_date"], dur, f"₱{s['price_per_night']:,.0f}",
                "⚠️ DUE TODAY"
            ), tags=("near_overdue",))

        for s in normal_stays:
            ci = datetime.strptime(s["check_in_date"], "%Y-%m-%d").date()
            co = datetime.strptime(s["check_out_date"], "%Y-%m-%d").date()
            dur = f"{(co - ci).days} nights"
            tree.insert("", "end", values=(
                f"Room {s['room_number']}", s["customer_name"], s["mobile_number"],
                s["check_in_date"], s["check_out_date"], dur, f"₱{s['price_per_night']:,.0f}",
                "Active Stay"
            ))

        add_table_filter(table_card, tree)()
        tree.pack(fill="both", expand=True)

    # =========================================================================
    # TAB 4: INVENTORY & GOODS RESTOCK (UTILITIES & KITCHEN)
    # =========================================================================
    def _render_inventory_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Hotel Inventory & Consumables Restock", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        btn_row = tk.Frame(top_bar, bg=COLOR_BG)
        btn_row.pack(side="right")

        tk.Button(
            btn_row,
            text="+ Add New Inventory Item",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._show_add_inventory_modal
        ).pack(side="left", padx=4)

        # Table Card
        table_card = tk.Frame(self.content_container, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        table_card.pack(fill="both", expand=True)

        # Filter bar
        filt_f = tk.Frame(table_card, bg=COLOR_WHITE)
        filt_f.pack(fill="x", pady=(0, 8))

        tk.Label(filt_f, text="Category:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(side="left")

        cat_var = tk.StringVar(value="All")
        for c_opt in ["All", "Kitchen", "Utility", "Low Stock Alert"]:
            tk.Radiobutton(
                filt_f, text=c_opt, variable=cat_var, value=c_opt,
                command=lambda: populate_inv(cat_var.get()),
                indicatoron=0, padx=8, pady=3, bg=COLOR_WHITE, selectcolor=COLOR_PRIMARY_TINT,
                fg=COLOR_PRIMARY, relief="flat", highlightthickness=1, highlightbackground=COLOR_BORDER,
                font=(FONT_FAMILY, 8, "bold"), cursor="hand2"
            ).pack(side="left", padx=4)

        cols = ("id", "name", "cat", "qty", "unit", "thresh", "cost", "status")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=13)

        tree.heading("id", text="ID")
        tree.heading("name", text="Item Name")
        tree.heading("cat", text="Category")
        tree.heading("qty", text="Quantity")
        tree.heading("unit", text="Unit")
        tree.heading("thresh", text="Threshold")
        tree.heading("cost", text="Cost/Unit")
        tree.heading("status", text="Stock Status")

        tree.column("id", width=40, anchor="center")
        tree.column("name", width=220, anchor="w")
        tree.column("cat", width=90, anchor="center")
        tree.column("qty", width=80, anchor="e")
        tree.column("unit", width=60, anchor="center")
        tree.column("thresh", width=80, anchor="e")
        tree.column("cost", width=90, anchor="e")
        tree.column("status", width=110, anchor="center")

        tree.tag_configure("low", background=COLOR_DANGER_BG, foreground=COLOR_DANGER_TEXT)

        def populate_inv(cat_filter):
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                items = conn.execute("SELECT * FROM inventory ORDER BY quantity ASC").fetchall()

            for itm in items:
                is_low = itm["quantity"] <= itm["low_stock_threshold"]
                if cat_filter == "Kitchen" and itm["category"] != "Kitchen":
                    continue
                if cat_filter == "Utility" and itm["category"] != "Utility":
                    continue
                if cat_filter == "Low Stock Alert" and not is_low:
                    continue

                status_txt = "⚠️ LOW STOCK" if is_low else "Normal"
                tag = ("low",) if is_low else ()

                tree.insert("", "end", values=(
                    itm["id"], itm["item_name"], itm["category"], itm["quantity"],
                    itm["unit"] or "units", itm["low_stock_threshold"], f"₱{itm['cost_per_unit'] or 50:.2f}",
                    status_txt
                ), tags=tag)

        refresh_inventory_filter = add_table_filter(table_card, tree)
        original_populate_inv = populate_inv
        def populate_inv_with_filter(cat_filter):
            original_populate_inv(cat_filter)
            refresh_inventory_filter()
        populate_inv = populate_inv_with_filter
        populate_inv(cat_var.get())
        tree.pack(fill="both", expand=True)

        # Bottom Restock Action Bar
        act_bar = tk.Frame(table_card, bg=COLOR_WHITE)
        act_bar.pack(fill="x", pady=(10, 0))

        def restock_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Item", "Please select an inventory item to restock.")
                return
            vals = tree.item(sel[0])["values"]
            self._show_restock_modal(vals[0], vals[1], vals[3], vals[4], lambda: populate_inv(cat_var.get()))

        restock_btn = tk.Button(
            act_bar,
            text="📥 Restock Selected Goods",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_SUCCESS,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=restock_selected
        )
        restock_btn.pack(side="left")

    def _show_add_inventory_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Add New Inventory Item")
        modal.geometry("400x380")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="NEW INVENTORY ITEM", font=(FONT_FAMILY, 12, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=20)
        form.pack(fill="both", expand=True)

        entries = {}
        fields = [
            ("Item Name", "name"),
            ("Quantity", "qty"),
            ("Low Threshold", "thresh"),
            ("Unit (e.g. g, ml, sets)", "unit"),
            ("Cost Per Unit (PHP)", "cost")
        ]
        for lbl, key in fields:
            f = tk.Frame(form, bg=COLOR_WHITE)
            f.pack(fill="x", pady=4)
            tk.Label(f, text=f"{lbl}:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_NORMAL, width=16, anchor="w", bg=COLOR_WHITE).pack(side="left")
            e = tk.Entry(f, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
            e.pack(side="left", fill="x", expand=True, ipady=3)
            entries[key] = e

        # Category
        cat_f = tk.Frame(form, bg=COLOR_WHITE)
        cat_f.pack(fill="x", pady=4)
        tk.Label(cat_f, text="Category:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_NORMAL, width=16, anchor="w", bg=COLOR_WHITE).pack(side="left")
        cat_var = tk.StringVar(value="Kitchen")
        cat_combo = ttk.Combobox(cat_f, textvariable=cat_var, values=["Kitchen", "Utility"], state="readonly")
        cat_combo.pack(side="left", fill="x", expand=True)

        def save_item():
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("Missing Info", "Item name is required.")
                return
            try:
                qty = int(entries["qty"].get() or 100)
                thresh = int(entries["thresh"].get() or 10)
                unit = entries["unit"].get().strip() or "units"
                cost = float(entries["cost"].get() or 50.0)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values.")
                return

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO inventory (item_name, category, quantity, low_stock_threshold, unit, cost_per_unit)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, cat_var.get(), qty, thresh, unit, cost))
                conn.commit()

            messagebox.showinfo("Success", f"Item '{name}' added to inventory!")
            modal.destroy()
            self._switch_tab("inventory")

        tk.Button(modal, text="Save Item", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=16, pady=6, command=save_item).pack(pady=12)

    def _show_restock_modal(self, item_id, item_name, cur_qty, unit, refresh_cb):
        modal = tk.Toplevel(self)
        modal.title("Restock Goods")
        modal.geometry("360x260")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text=f"RESTOCK: {item_name.upper()}", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)
        tk.Label(modal, text=f"Current Stock: {cur_qty} {unit}", font=(FONT_FAMILY, 10), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack()

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25, pady=10)
        form.pack(fill="x")

        tk.Label(form, text="Quantity to Add:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w", pady=(0, 4))
        qty_entry = tk.Entry(form, font=(FONT_FAMILY, 11), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        qty_entry.pack(fill="x", ipady=4)
        qty_entry.insert(0, "50")

        def apply_restock():
            try:
                add_qty = int(qty_entry.get())
                if add_qty <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Invalid Quantity", "Please enter a positive whole number.")
                return

            with get_connection() as conn:
                conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE id = ?", (add_qty, item_id))
                # Record transaction cost
                cost_per = conn.execute("SELECT cost_per_unit, category FROM inventory WHERE id = ?", (item_id,)).fetchone()
                cost_amt = add_qty * (cost_per["cost_per_unit"] or 25.0)
                tx_type = "Cost_Utility" if cost_per["category"] == "Utility" else "Cost_Goods"
                conn.execute("""
                    INSERT INTO transactions (type, amount, description, date_recorded)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (tx_type, cost_amt, f"Restocked {add_qty} {unit} of {item_name}"))
                conn.commit()

            messagebox.showinfo("Restocked", f"Successfully added {add_qty} {unit} to {item_name}!\nCost recorded: PHP {cost_amt:,.2f}")
            modal.destroy()
            refresh_cb()

        tk.Button(modal, text="Confirm Restock & Record Cost", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_SUCCESS, fg=COLOR_WHITE, relief="flat", padx=14, pady=6, command=apply_restock).pack(pady=14)

    # =========================================================================
    # TAB 5: STAFF MANAGEMENT (USER MANAGEMENT WITH PROFILE PHOTOS)
    # =========================================================================
    def _render_users_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Staff & Employee Directory", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        tk.Button(
            top_bar,
            text="+ Enroll New Staff Member",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._show_add_staff_modal
        ).pack(side="right")

        table_card = tk.Frame(self.content_container, bg=COLOR_BG)
        table_card.pack(fill="both", expand=True)

        # Left pane: Staff Table
        left_table_f = tk.Frame(table_card, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        left_table_f.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cols = ("id", "name", "role", "username", "phone", "email", "status")
        tree = ttk.Treeview(left_table_f, columns=cols, show="headings", height=14)

        tree.heading("id", text="ID")
        tree.heading("name", text="Full Name")
        tree.heading("role", text="Role")
        tree.heading("username", text="Username")
        tree.heading("phone", text="Phone")
        tree.heading("email", text="Email")
        tree.heading("status", text="Account Status")

        tree.column("id", width=35, anchor="center")
        tree.column("name", width=140, anchor="w")
        tree.column("role", width=110, anchor="center")
        tree.column("username", width=110, anchor="w")
        tree.column("phone", width=120, anchor="center")
        tree.column("email", width=160, anchor="w")
        tree.column("status", width=85, anchor="center")

        # Right pane: Highlighted Staff Picture Box & Profile Card
        right_profile_f = tk.Frame(table_card, bg=COLOR_WHITE, width=280, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        right_profile_f.pack(side="right", fill="y")
        right_profile_f.pack_propagate(False)

        tk.Label(
            right_profile_f,
            text="STAFF PICTURE & PROFILE",
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 10))

        # Photo Container Box with prominent accent border
        photo_box = tk.Frame(
            right_profile_f,
            bg=COLOR_BG,
            width=150,
            height=150,
            highlightthickness=2,
            highlightbackground=COLOR_ACCENT
        )
        photo_box.pack_propagate(False)
        photo_box.pack(pady=(0, 10))

        staff_photo_lbl = tk.Label(photo_box, bg=COLOR_BG)
        staff_photo_lbl.pack(fill="both", expand=True)

        lbl_s_name = tk.Label(right_profile_f, text="Select a Staff", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE, wraplength=250)
        lbl_s_name.pack(pady=(0, 3))

        lbl_s_role = tk.Label(right_profile_f, text="-", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_ACCENT_TEXT, bg=COLOR_ACCENT_LIGHT, padx=8, pady=2)
        lbl_s_role.pack(pady=(0, 8))

        detail_box = tk.Frame(right_profile_f, bg=COLOR_BG, padx=8, pady=8)
        detail_box.pack(fill="x", pady=(0, 10))

        lbl_s_id = tk.Label(detail_box, text="ID: -", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_NORMAL, bg=COLOR_BG, anchor="w")
        lbl_s_id.pack(fill="x", pady=1)

        lbl_s_uname = tk.Label(detail_box, text="Username: -", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_NORMAL, bg=COLOR_BG, anchor="w")
        lbl_s_uname.pack(fill="x", pady=1)

        lbl_s_phone = tk.Label(detail_box, text="Phone: -", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_NORMAL, bg=COLOR_BG, anchor="w")
        lbl_s_phone.pack(fill="x", pady=1)

        lbl_s_email = tk.Label(detail_box, text="Email: -", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_NORMAL, bg=COLOR_BG, anchor="w")
        lbl_s_email.pack(fill="x", pady=1)

        lbl_s_status = tk.Label(detail_box, text="Status: -", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_SUCCESS, bg=COLOR_BG, anchor="w")
        lbl_s_status.pack(fill="x", pady=1)

        current_loaded_photo = [None]

        def on_staff_select(event=None):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0])["values"]
            user_id = vals[0]
            with get_connection() as conn:
                r = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not r:
                return

            img_path = r["image_path"] or "assets/imgs/employees/m/1.jpg"
            img = load_image(img_path, (140, 140), preserve_aspect=True)
            current_loaded_photo[0] = img
            staff_photo_lbl.configure(image=img)

            lbl_s_name.config(text=r["name"])
            lbl_s_role.config(text=f"ROLE: {r['role'].upper()}")
            lbl_s_id.config(text=f"Employee ID: #{r['id']:02d}")
            lbl_s_uname.config(text=f"Username: {r['username']}")
            lbl_s_phone.config(text=f"Mobile: {r['phone'] or 'N/A'}")
            lbl_s_email.config(text=f"Email: {r['email'] or 'N/A'}")
            st = "Active" if r["is_active"] else "Inactive"
            lbl_s_status.config(
                text=f"Status: {st}",
                fg=COLOR_SUCCESS if r["is_active"] else COLOR_DANGER
            )

        tree.bind("<<TreeviewSelect>>", on_staff_select)

        def load_staff():
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
            for r in rows:
                st = "Active" if r["is_active"] else "Inactive"
                tree.insert("", "end", values=(
                    r["id"], r["name"], r["role"], r["username"], r["phone"] or "N/A",
                    r["email"] or "N/A", st
                ))
            children = tree.get_children()
            if children:
                tree.selection_set(children[0])
                tree.focus(children[0])
                on_staff_select(None)

        refresh_staff_filter = add_table_filter(left_table_f, tree)
        load_staff()
        refresh_staff_filter()
        tree.pack(fill="both", expand=True)

        # Action Buttons
        btn_f = tk.Frame(left_table_f, bg=COLOR_WHITE)
        btn_f.pack(fill="x", pady=(10, 0))

        def call_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Staff", "Please select a staff member to call.")
                return
            vals = tree.item(sel[0])["values"]
            user_id = vals[0]
            with get_connection() as conn:
                user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if user_row:
                PhoneCallModal(self, user_row["name"], user_row["phone"], user_row["role"], user_row["image_path"], user_row["id"])

        tk.Button(
            btn_f,
            text="📞 Call Staff Member",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=call_selected
        ).pack(side="left", padx=4)

        def edit_selected():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Staff", "Please select a staff member to edit.")
                return
            user_id = tree.item(sel[0])["values"][0]
            self._show_edit_staff_modal(user_id, load_staff)

        tk.Button(
            btn_f,
            text="✏️ Edit Staff Details",
            font=(FONT_FAMILY, 9),
            bg=COLOR_PRIMARY_TINT,
            fg=COLOR_PRIMARY,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=edit_selected
        ).pack(side="left", padx=4)

        def toggle_status():
            sel = tree.selection()
            if not sel:
                return
            user_id = tree.item(sel[0])["values"][0]
            with get_connection() as conn:
                conn.execute("UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id = ?", (user_id,))
                conn.commit()
            load_staff()
            refresh_staff_filter()

        tk.Button(
            btn_f,
            text="Toggle Active / Inactive",
            font=(FONT_FAMILY, 9),
            bg=COLOR_BG,
            fg=COLOR_TEXT_NORMAL,
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=toggle_status
        ).pack(side="left", padx=4)

    def _show_add_staff_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Enroll New Employee")
        modal.geometry("440x480")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="ENROLL NEW STAFF MEMBER", font=(FONT_FAMILY, 12, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25)
        form.pack(fill="both", expand=True)

        entries = {}
        fields = [
            ("Full Name", "name"),
            ("Username", "username"),
            ("Password", "password"),
            ("Phone Number", "phone"),
            ("Email", "email"),
            ("Image Path (e.g. assets/imgs/employees/m/1.jpg)", "img")
        ]
        for lbl, key in fields:
            f = tk.Frame(form, bg=COLOR_WHITE)
            f.pack(fill="x", pady=3)
            tk.Label(f, text=f"{lbl}:", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_TEXT_NORMAL, width=18, anchor="w", bg=COLOR_WHITE).pack(side="left")
            e = tk.Entry(f, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
            e.pack(side="left", fill="x", expand=True, ipady=3)
            entries[key] = e

        # Role Dropdown
        rf = tk.Frame(form, bg=COLOR_WHITE)
        rf.pack(fill="x", pady=3)
        tk.Label(rf, text="Assigned Role:", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_TEXT_NORMAL, width=18, anchor="w", bg=COLOR_WHITE).pack(side="left")
        role_var = tk.StringVar(value="Staff_Kitchen")
        cb = ttk.Combobox(rf, textvariable=role_var, values=["Admin", "Cashier", "Staff_Kitchen", "Staff_Logistics", "Staff_Utilities"], state="readonly")
        cb.pack(side="left", fill="x", expand=True)

        def save_staff():
            name = entries["name"].get().strip()
            uname = entries["username"].get().strip()
            pwd = entries["password"].get()
            phone = entries["phone"].get().strip()
            email = entries["email"].get().strip()
            img = entries["img"].get().strip() or "assets/imgs/employees/m/1.jpg"

            if not name or not uname or not pwd:
                messagebox.showwarning("Missing Info", "Name, Username, and Password are required.")
                return

            import hashlib, secrets
            salt = secrets.token_bytes(16)
            hashed = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, 100_000)
            pwd_hash = f"{salt.hex()}${hashed.hex()}"

            try:
                with get_connection() as conn:
                    conn.execute("""
                        INSERT INTO users (username, password_hash, role, name, phone, email, image_path, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """, (uname, pwd_hash, role_var.get(), name, phone, email, img))
                    conn.commit()

                messagebox.showinfo("Success", f"Employee {name} enrolled successfully!")
                modal.destroy()
                self._switch_tab("users")
            except Exception as e:
                messagebox.showerror("Error", f"Could not enroll staff: {e}")

        tk.Button(modal, text="Save Employee", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=16, pady=6, command=save_staff).pack(pady=12)

    def _show_edit_staff_modal(self, user_id, refresh_cb):
        with get_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return

        modal = tk.Toplevel(self)
        modal.title(f"Edit Staff: {user['name']}")
        modal.geometry("420x420")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text=f"EDIT EMPLOYEE #{user_id}", font=(FONT_FAMILY, 12, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25)
        form.pack(fill="both", expand=True)

        entries = {}
        fields = [
            ("Full Name", "name", user["name"]),
            ("Phone Number", "phone", user["phone"] or ""),
            ("Email", "email", user["email"] or ""),
            ("Image Path", "img", user["image_path"] or "")
        ]
        for lbl, key, val in fields:
            f = tk.Frame(form, bg=COLOR_WHITE)
            f.pack(fill="x", pady=4)
            tk.Label(f, text=f"{lbl}:", font=(FONT_FAMILY, 9, "bold"), width=14, anchor="w", bg=COLOR_WHITE).pack(side="left")
            e = tk.Entry(f, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
            e.pack(side="left", fill="x", expand=True, ipady=3)
            e.insert(0, val)
            entries[key] = e

        # Role
        rf = tk.Frame(form, bg=COLOR_WHITE)
        rf.pack(fill="x", pady=4)
        tk.Label(rf, text="Assigned Role:", font=(FONT_FAMILY, 9, "bold"), width=14, anchor="w", bg=COLOR_WHITE).pack(side="left")
        role_var = tk.StringVar(value=user["role"])
        cb = ttk.Combobox(rf, textvariable=role_var, values=["Admin", "Cashier", "Staff_Kitchen", "Staff_Logistics", "Staff_Utilities"], state="readonly")
        cb.pack(side="left", fill="x", expand=True)

        def save_edit():
            with get_connection() as conn:
                conn.execute("""
                    UPDATE users
                    SET name = ?, phone = ?, email = ?, image_path = ?, role = ?
                    WHERE id = ?
                """, (entries["name"].get().strip(), entries["phone"].get().strip(), entries["email"].get().strip(), entries["img"].get().strip(), role_var.get(), user_id))
                conn.commit()
            messagebox.showinfo("Updated", "Staff details updated successfully.")
            modal.destroy()
            refresh_cb()

        tk.Button(modal, text="Update Employee Details", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=14, pady=6, command=save_edit).pack(pady=14)

    # =========================================================================
    # TAB 6: CUSTOMER MANAGEMENT & LOYALTY (RUD)
    # =========================================================================
    def _render_customers_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Guest & Customer Loyalty Records (RUD)", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        table_card = tk.Frame(self.content_container, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        table_card.pack(fill="both", expand=True)

        cols = ("id", "name", "email", "phone", "points", "tier")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=14)

        tree.heading("id", text="ID")
        tree.heading("name", text="Guest Name")
        tree.heading("email", text="Email Address")
        tree.heading("phone", text="Mobile Number")
        tree.heading("points", text="Loyalty Points")
        tree.heading("tier", text="Membership Tier")

        tree.column("id", width=40, anchor="center")
        tree.column("name", width=170, anchor="w")
        tree.column("email", width=200, anchor="w")
        tree.column("phone", width=130, anchor="center")
        tree.column("points", width=110, anchor="e")
        tree.column("tier", width=110, anchor="center")

        def load_customers():
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                custs = conn.execute("SELECT * FROM customers ORDER BY loyalty_points DESC").fetchall()
            for c in custs:
                pts = c["loyalty_points"] or 0
                if pts >= 1500:
                    tier = "💎 Platinum VIP"
                elif pts >= 800:
                    tier = "🥇 Gold Member"
                elif pts >= 400:
                    tier = "🥈 Silver Tier"
                else:
                    tier = "Standard"

                tree.insert("", "end", values=(
                    c["id"], c["name"], c["email"] or "N/A", c["mobile_number"] or "N/A",
                    f"{pts:,} pts", tier
                ))

        refresh_customer_filter = add_table_filter(table_card, tree)
        load_customers()
        refresh_customer_filter()
        tree.pack(fill="both", expand=True)

        # Action Buttons
        btn_f = tk.Frame(table_card, bg=COLOR_WHITE)
        btn_f.pack(fill="x", pady=(10, 0))

        def edit_loyalty():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select Guest", "Please select a guest from the table.")
                return
            c_id = tree.item(sel[0])["values"][0]
            self._show_edit_customer_modal(c_id, load_customers)

        tk.Button(
            btn_f,
            text="⭐ Adjust Loyalty Points / Edit Guest",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_ACCENT,
            fg=COLOR_ACCENT_TEXT,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=edit_loyalty
        ).pack(side="left", padx=4)

    def _show_edit_customer_modal(self, cust_id, refresh_cb):
        with get_connection() as conn:
            cust = conn.execute("SELECT * FROM customers WHERE id = ?", (cust_id,)).fetchone()
        if not cust:
            return

        modal = tk.Toplevel(self)
        modal.title(f"Manage Guest: {cust['name']}")
        modal.geometry("400x380")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text=f"MANAGE GUEST LOYALTY: {cust['name'].upper()}", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25)
        form.pack(fill="both", expand=True)

        fields = [
            ("Full Name", "name", cust["name"]),
            ("Email", "email", cust["email"] or ""),
            ("Mobile Phone", "phone", cust["mobile_number"] or ""),
            ("Loyalty Points", "pts", str(cust["loyalty_points"] or 0))
        ]
        entries = {}
        for lbl, key, val in fields:
            f = tk.Frame(form, bg=COLOR_WHITE)
            f.pack(fill="x", pady=4)
            tk.Label(f, text=f"{lbl}:", font=(FONT_FAMILY, 9, "bold"), width=14, anchor="w", bg=COLOR_WHITE).pack(side="left")
            e = tk.Entry(f, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
            e.pack(side="left", fill="x", expand=True, ipady=3)
            e.insert(0, val)
            entries[key] = e

        def save_cust():
            try:
                pts = int(entries["pts"].get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Loyalty points must be a whole number.")
                return

            with get_connection() as conn:
                conn.execute("""
                    UPDATE customers
                    SET name = ?, email = ?, mobile_number = ?, loyalty_points = ?
                    WHERE id = ?
                """, (entries["name"].get().strip(), entries["email"].get().strip(), entries["phone"].get().strip(), pts, cust_id))
                conn.commit()

            messagebox.showinfo("Updated", f"Guest {cust['name']} updated with {pts} loyalty points!")
            modal.destroy()
            refresh_cb()

        tk.Button(modal, text="Save Guest & Points", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=14, pady=6, command=save_cust).pack(pady=14)

    # =========================================================================
    # TAB 7: LOYALTY REWARDS / PROMOTIONAL ATTAINMENTS
    # =========================================================================
    def _render_rewards_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Promotional Attainments & Loyalty Rewards", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        tk.Button(
            top_bar,
            text="+ Add New Loyalty Reward",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._show_add_reward_modal
        ).pack(side="right")

        table_card = tk.Frame(self.content_container, bg=COLOR_WHITE, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        table_card.pack(fill="both", expand=True)

        cols = ("id", "name", "points", "desc")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=14)

        tree.heading("id", text="ID")
        tree.heading("name", text="Reward Name / Promotional Attainment")
        tree.heading("points", text="Points Required")
        tree.heading("desc", text="Perk & Offer Description")

        tree.column("id", width=40, anchor="center")
        tree.column("name", width=240, anchor="w")
        tree.column("points", width=120, anchor="center")
        tree.column("desc", width=420, anchor="w")

        def load_rewards():
            for i in tree.get_children():
                tree.delete(i)
            with get_connection() as conn:
                rewards = conn.execute("SELECT * FROM loyalty_rewards ORDER BY points_required ASC").fetchall()
            for r in rewards:
                tree.insert("", "end", values=(
                    r["id"], r["reward_name"], f"{r['points_required']} pts", r["description"]
                ))

        refresh_reward_filter = add_table_filter(table_card, tree)
        load_rewards()
        refresh_reward_filter()
        tree.pack(fill="both", expand=True)

        # Actions
        act_f = tk.Frame(table_card, bg=COLOR_WHITE)
        act_f.pack(fill="x", pady=(10, 0))

        def delete_reward():
            sel = tree.selection()
            if not sel:
                return
            r_id = tree.item(sel[0])["values"][0]
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this promotional reward?"):
                with get_connection() as conn:
                    conn.execute("DELETE FROM loyalty_rewards WHERE id = ?", (r_id,))
                    conn.commit()
                load_rewards()

        tk.Button(act_f, text="🗑️ Delete Reward", font=(FONT_FAMILY, 9), bg=COLOR_DANGER, fg=COLOR_WHITE, relief="flat", padx=10, pady=4, command=delete_reward).pack(side="left")

    def _show_add_reward_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Add Promotional Reward")
        modal.geometry("380x320")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="NEW PROMOTIONAL ATTAINMENT", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Reward Name:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        name_e = tk.Entry(form, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        name_e.pack(fill="x", ipady=3, pady=(2, 8))

        tk.Label(form, text="Points Required:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        pts_e = tk.Entry(form, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        pts_e.pack(fill="x", ipady=3, pady=(2, 8))
        pts_e.insert(0, "200")

        tk.Label(form, text="Description:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        desc_e = tk.Entry(form, font=(FONT_FAMILY, 9), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        desc_e.pack(fill="x", ipady=3, pady=(2, 8))

        def save_r():
            name = name_e.get().strip()
            desc = desc_e.get().strip()
            try:
                pts = int(pts_e.get())
            except ValueError:
                messagebox.showerror("Error", "Points must be a valid number.")
                return
            if not name:
                messagebox.showwarning("Missing Info", "Reward name is required.")
                return

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO loyalty_rewards (reward_name, points_required, description)
                    VALUES (?, ?, ?)
                """, (name, pts, desc))
                conn.commit()

            messagebox.showinfo("Saved", f"Promotional reward '{name}' added successfully!")
            modal.destroy()
            self._switch_tab("rewards")

        tk.Button(modal, text="Save Reward", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=14, pady=6, command=save_r).pack(pady=10)

    # =========================================================================
    # TAB 8: EMPLOYEE BULLETIN ANNOUNCEMENTS
    # =========================================================================
    def _render_bulletin_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Employee Bulletin & Staff Announcements", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        tk.Button(
            top_bar,
            text="📢 Post New Hotel Announcement",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
            command=self._show_post_bulletin_modal
        ).pack(side="right")

        # Scrollable container of bulletin cards
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

            tk.Label(
                card,
                text=f"By: {p['author_name']} ({p['author_role']})",
                font=(FONT_FAMILY, 8, "bold"),
                fg=COLOR_ACCENT,
                bg=COLOR_WHITE
            ).pack(anchor="w", pady=(0, 6))

            tk.Label(
                card,
                text=p["content"],
                font=(FONT_FAMILY, 9),
                fg=COLOR_TEXT_NORMAL,
                bg=COLOR_WHITE,
                wraplength=700,
                justify="left"
            ).pack(anchor="w")

    def _show_post_bulletin_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Post Announcement")
        modal.geometry("440x360")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="BROADCAST BULLETIN ANNOUNCEMENT", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=25)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Headline / Title:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        title_e = tk.Entry(form, font=(FONT_FAMILY, 10), bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        title_e.pack(fill="x", ipady=4, pady=(2, 10))

        tk.Label(form, text="Announcement Content:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        txt = tk.Text(form, font=(FONT_FAMILY, 9), height=6, bg=COLOR_BG, highlightthickness=1, highlightbackground=COLOR_BORDER)
        txt.pack(fill="both", expand=True, pady=(2, 10))

        def publish():
            t = title_e.get().strip()
            c = txt.get("1.0", "end").strip()
            if not t or not c:
                messagebox.showwarning("Missing Content", "Title and content are required.")
                return

            with get_connection() as conn:
                conn.execute("""
                    INSERT INTO bulletin (author_id, title, content, timestamp)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (self.current_user["id"], t, c))
                conn.commit()

            messagebox.showinfo("Published", "Announcement posted to employee bulletin!")
            modal.destroy()
            self._switch_tab("bulletin")

        tk.Button(modal, text="Broadcast to All Staff", font=(FONT_FAMILY, 10, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", padx=16, pady=6, command=publish).pack(pady=12)

    # =========================================================================
    # TAB 9: EMPLOYEE INBOX & DISPATCH (WITH VOICE CALL)
    # =========================================================================
    def _render_inbox_tab(self):
        # Two pane: Left Staff Directory (with Call buttons), Right Message Feed
        panes = tk.Frame(self.content_container, bg=COLOR_BG)
        panes.pack(fill="both", expand=True)
        panes.columnconfigure(0, weight=4)
        panes.columnconfigure(1, weight=6)

        # Left: Staff Contact Directory
        left_card = tk.Frame(panes, bg=COLOR_WHITE, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(left_card, text="STAFF SPEED DIAL & DIRECTORY", font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 8))

        directory_search = tk.StringVar()
        tk.Label(left_card, text="Search staff:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")
        tk.Entry(left_card, textvariable=directory_search, font=FONT_SMALL, relief="solid", bd=1).pack(fill="x", pady=(2, 8), ipady=4)
        directory_rows = []

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

        for s in staff_rows:
            row_box = tk.Frame(s_list, bg=COLOR_WHITE, pady=4, highlightthickness=1, highlightbackground=COLOR_BORDER)
            row_box.pack(fill="x", pady=2)
            directory_rows.append((row_box, f"{s['name']} {s['role']} {s['phone'] or ''}".casefold()))

            info_f = tk.Frame(row_box, bg=COLOR_WHITE)
            info_f.pack(side="left", padx=6)

            tk.Label(info_f, text=s["name"], font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_NORMAL, bg=COLOR_WHITE).pack(anchor="w")
            tk.Label(info_f, text=f"{s['role']}  •  {s['phone'] or 'N/A'}", font=(FONT_FAMILY, 8), fg=COLOR_TEXT_MUTED, bg=COLOR_WHITE).pack(anchor="w")

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
                command=lambda name=s["name"], ph=s["phone"], role=s["role"], img=s["image_path"], uid=s["id"]: PhoneCallModal(self, name, ph, role, img, uid)
            )
            call_btn.pack(side="right", padx=6)

        def filter_directory(*_):
            query = directory_search.get().strip().casefold()
            for row_box, text in directory_rows:
                if query in text:
                    row_box.pack(fill="x", pady=2)
                else:
                    row_box.pack_forget()

        directory_search.trace_add("write", filter_directory)

        # Right: Message Threads & Dispatch
        right_card = tk.Frame(panes, bg=COLOR_WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        tk.Label(right_card, text="STAFF DISPATCH INBOX & MESSAGES", font=(FONT_FAMILY, 10, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(anchor="w", pady=(0, 6))

        # Compose button
        tk.Button(
            right_card,
            text="+ Send Message to Staff / Department",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._show_send_message_modal
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
        message_search.set("")
        message_cards = []

        # Messages list
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

    def _show_send_message_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Send Staff Message")
        modal.geometry("400x340")
        modal.configure(bg=COLOR_WHITE)
        modal.transient(self)
        modal.grab_set()

        tk.Label(modal, text="DISPATCH STAFF MESSAGE", font=(FONT_FAMILY, 11, "bold"), fg=COLOR_PRIMARY, bg=COLOR_WHITE).pack(pady=12)

        form = tk.Frame(modal, bg=COLOR_WHITE, padx=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Send To Department / Role:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
        role_var = tk.StringVar(value="Staff_Kitchen")
        cb = ttk.Combobox(form, textvariable=role_var, values=["Staff_Kitchen", "Staff_Logistics", "Staff_Utilities", "Cashier", "Admin"], state="readonly")
        cb.pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Message Content:", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_WHITE).pack(anchor="w")
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

    # =========================================================================
    # TAB 10: SECURITY & AUTH LOGS (DECRYPTED) + HEALTH LOGS
    # =========================================================================
    def _render_logs_tab(self):
        top_bar = tk.Frame(self.content_container, bg=COLOR_BG)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Security Audit: Decrypted Auth & System Health Logs", font=FONT_HEADING, fg=COLOR_PRIMARY, bg=COLOR_BG).pack(side="left")

        # Two Tabs / Notebook inside
        nb = ttk.Notebook(self.content_container)
        nb.pack(fill="both", expand=True)

        # Sub-tab 1: Encrypted Auth Logs (Decrypted for Admin)
        f_auth = tk.Frame(nb, bg=COLOR_WHITE, padx=12, pady=10)
        nb.add(f_auth, text="🔐 Decrypted Authentication Logs (Logins & Lockouts)")

        tk.Label(
            f_auth,
            text="Decrypted real-time stream from logs/auth_logs.enc.txt (Protected by Enterprise Cipher):",
            font=(FONT_FAMILY, 9, "italic"),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 6))

        txt_auth = tk.Text(f_auth, font=("Consolas", 9), bg=COLOR_PRIMARY_DARK, fg="#E2E8F0", wrap="none")
        s_auth_y = ttk.Scrollbar(f_auth, orient="vertical", command=txt_auth.yview)
        s_auth_x = ttk.Scrollbar(f_auth, orient="horizontal", command=txt_auth.xview)
        txt_auth.configure(yscrollcommand=s_auth_y.set, xscrollcommand=s_auth_x.set)

        s_auth_y.pack(side="right", fill="y")
        s_auth_x.pack(side="bottom", fill="x")
        txt_auth.pack(fill="both", expand=True)

        # Load decrypted logs
        decrypted_entries = read_decrypted_auth_logs()
        if decrypted_entries:
            for entry in decrypted_entries:
                txt_auth.insert("end", entry + "\n")
        else:
            txt_auth.insert("end", "[No authentication log records found yet]\n")
        txt_auth.see("end")

        # Sub-tab 2: System Health Logs
        f_health = tk.Frame(nb, bg=COLOR_WHITE, padx=12, pady=10)
        nb.add(f_health, text="🩺 System Health & Telemetry Logs")

        tk.Label(
            f_health,
            text="Unencrypted runtime diagnostics, SQLite database metrics, and server telemetry:",
            font=(FONT_FAMILY, 9, "italic"),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_WHITE
        ).pack(anchor="w", pady=(0, 6))

        txt_health = tk.Text(f_health, font=("Consolas", 9), bg="#0F172A", fg="#38BDF8", wrap="none")
        s_health_y = ttk.Scrollbar(f_health, orient="vertical", command=txt_health.yview)
        txt_health.configure(yscrollcommand=s_health_y.set)

        s_health_y.pack(side="right", fill="y")
        txt_health.pack(fill="both", expand=True)

        health_data = read_system_health_logs()
        txt_health.insert("end", health_data)
        txt_health.see("end")
