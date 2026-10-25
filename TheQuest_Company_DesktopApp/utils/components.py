"""
Reusable UI Components and Widgets for The Quest Hotel Management System.
Includes:
- Softphone Call Simulation Dialog (PhoneCallModal)
- Interactive Hotel Map Canvas Widget (HotelMapWidget)
- Metric KPI Card (MetricCard)
- Modern Custom Buttons and Badges
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import re
from pathlib import Path
from PIL import Image, ImageTk

from .theme import (
    COLOR_PRIMARY, COLOR_PRIMARY_DARK, COLOR_PRIMARY_LIGHT, COLOR_PRIMARY_TINT,
    COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_ACCENT_LIGHT, COLOR_ACCENT_TEXT,
    COLOR_WHITE, COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT_DARK,
    COLOR_TEXT_NORMAL, COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_WARNING, COLOR_INFO, STATUS_COLORS, FONT_FAMILY, FONT_HEADING,
    FONT_SUBHEADING, FONT_TITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL,
    FONT_SMALL_BOLD, FONT_STAT_VAL, SYSTEM_SLOGAN,
    COLOR_DANGER_TEXT, COLOR_DANGER_BG,
    COLOR_WARNING_TEXT, COLOR_WARNING_BG,
    COLOR_INFO_TEXT, COLOR_INFO_BG,
    COLOR_SUCCESS_TEXT, COLOR_SUCCESS_BG
)
from .image_loader import load_image, get_hotel_map_image


def add_table_filter(parent, tree, columns=None):
    """Add a live text filter and column selector above a Treeview.

    The filter only hides existing rows, so it remains compatible with the
    page-specific loaders and does not alter the underlying database query.
    Call the returned ``refresh`` function after repopulating the Treeview.
    """
    columns = columns or list(tree["columns"])
    filter_frame = tk.Frame(parent, bg=COLOR_WHITE)
    filter_frame.pack(fill="x", pady=(0, 8))

    tk.Label(
        filter_frame,
        text="Search:",
        font=(FONT_FAMILY, 9, "bold"),
        fg=COLOR_TEXT_MUTED,
        bg=COLOR_WHITE
    ).pack(side="left")

    search_var = tk.StringVar()
    search_entry = tk.Entry(
        filter_frame,
        textvariable=search_var,
        font=FONT_SMALL,
        width=24,
        relief="solid",
        bd=1
    )
    search_entry.pack(side="left", padx=(6, 10), ipady=3)

    column_labels = ["All columns"] + [
        tree.heading(column, "text") or column for column in columns
    ]
    column_var = tk.StringVar(value=column_labels[0])
    column_menu = ttk.Combobox(
        filter_frame,
        textvariable=column_var,
        values=column_labels,
        state="readonly",
        width=18,
        font=FONT_SMALL
    )
    column_menu.pack(side="left", padx=(0, 8))

    all_items = []
    sort_column = None
    sort_reverse = False

    def sort_key(value):
        """Sort numeric-looking table values numerically and other values naturally."""
        text = str(value or "").strip()
        numeric_text = re.sub(r"[^\d.-]", "", text)
        try:
            return (0, float(numeric_text))
        except ValueError:
            return (1, text.casefold())

    def sort_by_column(column):
        nonlocal sort_column, sort_reverse

        if sort_column == column:
            sort_reverse = not sort_reverse
        else:
            sort_column = column
            sort_reverse = False

        sorted_items = sorted(
            all_items,
            key=lambda item_id: sort_key(tree.set(item_id, column)),
            reverse=sort_reverse
        )
        all_items[:] = sorted_items
        for index, item_id in enumerate(sorted_items):
            tree.move(item_id, "", index)
        apply_filter()

        for current_column in columns:
            heading = tree.heading(current_column, "text")
            heading = re.sub(r" [<>]$", "", heading)
            if current_column == column:
                heading += " <" if sort_reverse else " >"
            tree.heading(current_column, text=heading)

    for column in columns:
        tree.heading(
            column,
            command=lambda selected_column=column: sort_by_column(selected_column)
        )

    def refresh():
        for item_id in all_items:
            if tree.exists(item_id):
                tree.reattach(item_id, "", "end")
        all_items[:] = list(tree.get_children(""))
        apply_filter()

    def apply_filter(*_):
        query = search_var.get().strip().casefold()
        selected_column = column_var.get()
        selected_index = (
            column_labels.index(selected_column) - 1
            if selected_column != "All columns" else None
        )

        for item_id in all_items:
            values = tree.item(item_id, "values")
            haystack = (
                values[selected_index] if selected_index is not None
                and selected_index < len(values)
                else " ".join(str(value) for value in values)
            )
            matches = not query or query in str(haystack).casefold()
            if matches:
                tree.reattach(item_id, "", "end")
            else:
                tree.detach(item_id)

    search_var.trace_add("write", apply_filter)
    column_menu.bind("<<ComboboxSelected>>", apply_filter)

    def clear_filter():
        search_var.set("")
        column_var.set(column_labels[0])
        apply_filter()

    tk.Button(
        filter_frame,
        text="Clear",
        font=FONT_SMALL_BOLD,
        bg=COLOR_PRIMARY_TINT,
        fg=COLOR_PRIMARY,
        relief="flat",
        padx=8,
        pady=3,
        cursor="hand2",
        command=clear_filter
    ).pack(side="left")

    return refresh

class PhoneCallModal(tk.Toplevel):
    """
    Realistic interactive Softphone Call Dialog for calling employees or customers.
    Features: Ringing state, simulated pickup, live duration timer, mute/speaker toggles,
    and end call summary.
    """
    def __init__(
        self, parent, contact_name: str, phone_number: str,
        role_title: str = "Staff Member", image_path: str = None,
        receiver_id: int = None, call_id: int = None,
    ):
        super().__init__(parent)
        self.contact_name = contact_name
        self.phone_number = phone_number or "+63 900 000 0000"
        self.role_title = role_title
        self.image_path = image_path

        self.title("The Quest - Voice Dispatch")
        self.geometry("380x520")
        self.resizable(False, False)
        self.configure(bg=COLOR_PRIMARY_DARK)
        self.transient(parent)
        self.grab_set()

        self.is_connected = False
        self.call_start_time = None
        self.call_duration_seconds = 0
        self.is_muted = False
        self.timer_job = None
        self.ringtone_job = None
        self.is_ringing = False
        self.audio_stream = None
        self.call_id = call_id
        self.is_outgoing = receiver_id is not None
        self._parent_user_id = getattr(parent, "current_user", {}).get("id")

        if receiver_id and self._parent_user_id and not call_id:
            try:
                from database.db import get_connection
                with get_connection() as connection:
                    result = connection.execute(
                        "INSERT INTO calls (caller_id, receiver_id) VALUES (?, ?)",
                        (self._parent_user_id, receiver_id),
                    )
                    self.call_id = result.lastrowid
                    connection.commit()
            except Exception as error:
                messagebox.showerror("Call unavailable", f"Could not start the call:\n{error}")
                self.destroy()
                return

        self._build_ui()
        self._start_call_sequence()

    def _build_ui(self):
        # Top Header
        top_frame = tk.Frame(self, bg=COLOR_PRIMARY_DARK)
        top_frame.pack(fill="x", pady=(20, 10))

        tk.Label(
            top_frame,
            text="THE QUEST COMMUNICATIONS",
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_ACCENT,
            bg=COLOR_PRIMARY_DARK
        ).pack()

        self.status_label = tk.Label(
            top_frame,
            text="Connecting to Line...",
            font=(FONT_FAMILY, 11, "italic"),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY_DARK
        )
        self.status_label.pack(pady=4)

        # Contact Avatar
        avatar_frame = tk.Frame(self, bg=COLOR_PRIMARY_DARK)
        avatar_frame.pack(pady=10)

        photo = load_image(self.image_path, (110, 110), circular=True)
        avatar_lbl = tk.Label(avatar_frame, image=photo, bg=COLOR_PRIMARY_DARK)
        avatar_lbl.image = photo
        avatar_lbl.pack()

        # Contact Info
        tk.Label(
            self,
            text=self.contact_name,
            font=(FONT_FAMILY, 16, "bold"),
            fg=COLOR_WHITE,
            bg=COLOR_PRIMARY_DARK
        ).pack(pady=(5, 2))

        tk.Label(
            self,
            text=self.role_title,
            font=(FONT_FAMILY, 10),
            fg=COLOR_ACCENT,
            bg=COLOR_PRIMARY_DARK
        ).pack()

        tk.Label(
            self,
            text=self.phone_number,
            font=(FONT_FAMILY, 11),
            fg=COLOR_PRIMARY_TINT,
            bg=COLOR_PRIMARY_DARK
        ).pack(pady=4)

        # Duration Timer Display
        self.timer_label = tk.Label(
            self,
            text="00:00",
            font=(FONT_FAMILY, 22, "bold"),
            fg=COLOR_WHITE,
            bg=COLOR_PRIMARY_DARK
        )
        self.timer_label.pack(pady=15)

        # Softphone Action Controls
        ctrl_frame = tk.Frame(self, bg=COLOR_PRIMARY_DARK)
        ctrl_frame.pack(pady=10)

        self.mute_btn = tk.Button(
            ctrl_frame,
            text="🎤 Mute",
            font=(FONT_FAMILY, 10, "bold"),
            bg="#4A2374",
            fg=COLOR_WHITE,
            activebackground="#5E2C94",
            activeforeground=COLOR_WHITE,
            relief="flat",
            width=10,
            cursor="hand2",
            command=self._toggle_mute
        )
        self.mute_btn.pack(side="left", padx=8)

        self.speaker_btn = tk.Button(
            ctrl_frame,
            text="🔊 Speaker",
            font=(FONT_FAMILY, 10, "bold"),
            bg="#4A2374",
            fg=COLOR_WHITE,
            activebackground="#5E2C94",
            activeforeground=COLOR_WHITE,
            relief="flat",
            width=10,
            cursor="hand2"
        )
        self.speaker_btn.pack(side="left", padx=8)

        # End Call Button (Big Red Action)
        end_btn = tk.Button(
            self,
            text="End Call",
            font=(FONT_FAMILY, 12, "bold"),
            bg=COLOR_DANGER,
            fg=COLOR_WHITE,
            activebackground="#DC2626",
            activeforeground=COLOR_WHITE,
            relief="flat",
            width=20,
            height=2,
            cursor="hand2",
            command=self._end_call
        )
        end_btn.pack(pady=20)

    def _start_call_sequence(self):
        """Simulates line ringing then connecting after 1.5 seconds."""
        self.status_label.config(text="Dialing...")
        self.after(800, lambda: self.status_label.config(text="Ringing... 📳"))
        self.after(800, self._start_ringtone)
        self.after(2200, self._connect_call)

    def _start_ringtone(self):
        if not self.winfo_exists() or self.is_connected:
            return
        self.is_ringing = True
        self._ring_once()

    def _ring_once(self):
        if not self.is_ringing or not self.winfo_exists():
            return
        try:
            import winsound
            winsound.Beep(880, 180)
            winsound.Beep(660, 180)
        except (ImportError, RuntimeError):
            self.bell()
        self.ringtone_job = self.after(900, self._ring_once)

    def _stop_ringtone(self):
        self.is_ringing = False
        if self.ringtone_job:
            self.after_cancel(self.ringtone_job)
            self.ringtone_job = None

    def _connect_call(self):
        if not self.winfo_exists():
            return
        self._stop_ringtone()
        self.is_connected = True
        self.call_start_time = time.time()
        self.status_label.config(text="Connected (Microphone active) 🟢", fg=COLOR_SUCCESS)
        if self.call_id and not self.is_outgoing:
            try:
                from database.db import get_connection
                with get_connection() as connection:
                    connection.execute(
                        "UPDATE calls SET status = 'answered', answered_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (self.call_id,),
                    )
                    connection.commit()
            except Exception as error:
                messagebox.showerror("Call update failed", str(error))
        self._start_microphone()
        self._tick_timer()

    def _start_microphone(self):
        try:
            import sounddevice as sd

            def audio_callback(indata, outdata, _frames, _time_info, _status):
                if self.is_muted:
                    outdata.fill(0)
                else:
                    outdata[:] = indata

            self.audio_stream = sd.Stream(
                samplerate=44100, channels=1, dtype="float32",
                callback=audio_callback,
            )
            self.audio_stream.start()
        except (ImportError, OSError, RuntimeError, ValueError) as error:
            self.status_label.config(text="Connected (audio unavailable)", fg=COLOR_WARNING)
            messagebox.showwarning(
                "Microphone unavailable",
                f"The call is connected, but microphone loopback could not start:\n{error}\n\n"
                "Install the desktop requirements and check microphone permission.",
            )

    def _tick_timer(self):
        if not self.is_connected:
            return
        elapsed = int(time.time() - self.call_start_time)
        self.call_duration_seconds = elapsed
        mins, secs = divmod(elapsed, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        self.timer_job = self.after(1000, self._tick_timer)

    def _toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.mute_btn.config(text="🔇 Muted", bg=COLOR_WARNING, fg=COLOR_TEXT_DARK)
        else:
            self.mute_btn.config(text="🎤 Mute", bg="#4A2374", fg=COLOR_WHITE)

    def _end_call(self):
        self._stop_ringtone()
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.is_connected = False
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
        if self.call_id:
            try:
                from database.db import get_connection
                with get_connection() as connection:
                    connection.execute(
                        "UPDATE calls SET status = 'ended', ended_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (self.call_id,),
                    )
                    connection.commit()
            except Exception as error:
                messagebox.showerror("Call update failed", str(error))
        mins, secs = divmod(self.call_duration_seconds, 60)
        duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
        messagebox.showinfo(
            "Call Ended",
            f"Call with {self.contact_name} ({self.role_title}) has ended.\nDuration: {duration_str}"
        )
        self.destroy()


def monitor_incoming_calls(page):
    """Poll the shared database so desktop employees receive calls while online."""
    if not page.winfo_exists():
        return
    if not getattr(page, "_active_call_modal", None):
        try:
            from database.db import get_connection
            with get_connection() as connection:
                call = connection.execute(
                    "SELECT c.id, u.name, u.phone, u.role, u.image_path "
                    "FROM calls c JOIN users u ON u.id = c.caller_id "
                    "WHERE c.receiver_id = ? AND c.status = 'ringing' "
                    "ORDER BY c.created_at LIMIT 1",
                    (page.current_user["id"],),
                ).fetchone()
            if call:
                page._active_call_modal = PhoneCallModal(
                    page, call["name"], call["phone"], call["role"],
                    call["image_path"], call_id=call["id"],
                )
                page._active_call_modal.bind(
                    "<Destroy>", lambda _event: setattr(page, "_active_call_modal", None)
                )
        except Exception as error:
            messagebox.showerror("Incoming call error", str(error))
    page.after(2500, lambda: monitor_incoming_calls(page))


class MetricCard(tk.Frame):
    """Modern KPI metric card with purple/gold accents and clean typography."""
    def __init__(self, parent, title: str, value: str, subtext: str = "", badge: str = "", border_color: str = COLOR_BORDER, **kwargs):
        super().__init__(parent, bg=COLOR_CARD, highlightthickness=1, highlightbackground=border_color, **kwargs)
        
        inner = tk.Frame(self, bg=COLOR_CARD, padx=16, pady=12)
        inner.pack(fill="both", expand=True)

        top_row = tk.Frame(inner, bg=COLOR_CARD)
        top_row.pack(fill="x")

        tk.Label(
            top_row,
            text=title.upper(),
            font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD
        ).pack(side="left")

        if badge:
            badge_lbl = tk.Label(
                top_row,
                text=f" {badge} ",
                font=(FONT_FAMILY, 8, "bold"),
                bg=COLOR_PRIMARY_TINT,
                fg=COLOR_PRIMARY,
                padx=4,
                pady=1
            )
            badge_lbl.pack(side="right")

        self.val_label = tk.Label(
            inner,
            text=value,
            font=FONT_STAT_VAL,
            fg=COLOR_PRIMARY,
            bg=COLOR_CARD
        )
        self.val_label.pack(anchor="w", pady=(6, 2))

        if subtext:
            self.sub_label = tk.Label(
                inner,
                text=subtext,
                font=(FONT_FAMILY, 8),
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_CARD
            )
            self.sub_label.pack(anchor="w")

    def update_value(self, new_val: str, new_sub: str = None):
        self.val_label.config(text=new_val)
        if new_sub and hasattr(self, "sub_label"):
            self.sub_label.config(text=new_sub)


class HotelMapWidget(tk.Frame):
    """
    Comprehensive interactive Hotel Map visualizer for The Quest Hotel cross-section.
    Supports floor-by-floor view, occupied/reserved/vacant/needs-service filters,
    and clickable room inspection modals.
    """
    def __init__(self, parent, db_conn_func, on_room_click_cb=None, utilities_mode: bool = False):
        super().__init__(parent, bg=COLOR_BG)
        self.get_connection = db_conn_func
        self.on_room_click_cb = on_room_click_cb
        self.utilities_mode = utilities_mode  # If true, empty rooms are hidden

        self.current_view = "grid"
        self.hotel_map_photo = None
        self._build_ui()
        self.refresh_rooms()

    def _build_ui(self):
        # Header Controls & View Switcher
        ctrl_bar = tk.Frame(self, bg=COLOR_WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        ctrl_bar.pack(fill="x", pady=(0, 10))

        title_lbl = tk.Label(
            ctrl_bar,
            text="🏨 The Quest Hotel - Architectural Floor Status Map",
            font=(FONT_FAMILY, 12, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE
        )
        title_lbl.pack(side="left")

        # View Toggle Switcher (Grid View vs Architectural Blueprint Image)
        view_f = tk.Frame(ctrl_bar, bg=COLOR_WHITE)
        view_f.pack(side="left", padx=20)

        self.btn_grid_view = tk.Button(
            view_f,
            text="🏢 Floor & Room Status Grid",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: self._set_view_mode("grid")
        )
        self.btn_grid_view.pack(side="left", padx=(0, 4))

        self.btn_blueprint_view = tk.Button(
            view_f,
            text="🗺️ Architectural Blueprint Map",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_WHITE,
            fg=COLOR_PRIMARY,
            relief="solid",
            bd=1,
            padx=10,
            pady=4,
            cursor="hand2",
            command=lambda: self._set_view_mode("blueprint")
        )
        self.btn_blueprint_view.pack(side="left")

        # Legend Badges
        legend_frame = tk.Frame(ctrl_bar, bg=COLOR_WHITE)
        legend_frame.pack(side="right")

        legends = [
            ("Vacant", COLOR_SUCCESS),
            ("Occupied", COLOR_DANGER),
            ("Needs Service", COLOR_WARNING),
            ("Reserved", COLOR_INFO)
        ]
        for name, color in legends:
            dot = tk.Label(legend_frame, text="●", font=(FONT_FAMILY, 12), fg=color, bg=COLOR_WHITE)
            dot.pack(side="left", padx=(8, 2))
            lbl = tk.Label(legend_frame, text=name, font=(FONT_FAMILY, 9), fg=COLOR_TEXT_NORMAL, bg=COLOR_WHITE)
            lbl.pack(side="left")

        # Body Container for switching views
        self.body_container = tk.Frame(self, bg=COLOR_BG)
        self.body_container.pack(fill="both", expand=True)

        # ---------------- 1. GRID VIEW CONTAINER ----------------
        self.grid_view_frame = tk.Frame(self.body_container, bg=COLOR_BG)

        # Filter bar
        self.filter_bar = tk.Frame(self.grid_view_frame, bg=COLOR_BG)
        self.filter_bar.pack(fill="x", pady=(0, 10))

        tk.Label(self.filter_bar, text="Filter Rooms:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, bg=COLOR_BG).pack(side="left", padx=(4, 8))

        filter_opts = ["All", "Occupied", "Needs Service", "Reserved", "Vacant"]
        if self.utilities_mode:
            filter_opts = ["Occupied & Needs Service", "Occupied", "Needs Service"]

        self.filter_var = tk.StringVar(value=filter_opts[0])
        for opt in filter_opts:
            btn = tk.Radiobutton(
                self.filter_bar,
                text=opt,
                variable=self.filter_var,
                value=opt,
                command=self.refresh_rooms,
                indicatoron=0,
                padx=10,
                pady=4,
                font=(FONT_FAMILY, 9, "bold"),
                bg=COLOR_WHITE,
                selectcolor=COLOR_PRIMARY_TINT,
                fg=COLOR_PRIMARY,
                activebackground=COLOR_ACCENT_LIGHT,
                relief="flat",
                highlightthickness=1,
                highlightbackground=COLOR_BORDER,
                cursor="hand2"
            )
            btn.pack(side="left", padx=4)

        # Refresh button
        refresh_btn = tk.Button(
            self.filter_bar,
            text="🔄 Refresh Rooms",
            font=(FONT_FAMILY, 9, "bold"),
            bg=COLOR_PRIMARY,
            fg=COLOR_WHITE,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.refresh_rooms
        )
        refresh_btn.pack(side="right")

        # Scrollable Rooms Grid Container
        self.canvas = tk.Canvas(self.grid_view_frame, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.grid_view_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=COLOR_BG)

        self.scroll_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_win = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")
        self.canvas.configure(xscrollcommand=None, yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_win, width=e.width)
        )

        def _on_grid_wheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", _on_grid_wheel)

        # ---------------- 2. BLUEPRINT VIEW CONTAINER ----------------
        self.blueprint_view_frame = tk.Frame(self.body_container, bg=COLOR_BG)
        self._build_blueprint_ui()

        # Mount default view
        self.grid_view_frame.pack(fill="both", expand=True)

    def _build_blueprint_ui(self):
        # KPI Bar on Blueprint
        self.bp_kpi_bar = tk.Frame(self.blueprint_view_frame, bg=COLOR_WHITE, padx=16, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.bp_kpi_bar.pack(fill="x", pady=(0, 10))

        self.bp_kpi_label = tk.Label(
            self.bp_kpi_bar,
            text="Loading Hotel Capacity...",
            font=(FONT_FAMILY, 10, "bold"),
            fg=COLOR_PRIMARY,
            bg=COLOR_WHITE
        )
        self.bp_kpi_label.pack(side="left")

        # Scrollable Blueprint Canvas
        bp_canvas_f = tk.Frame(self.blueprint_view_frame, bg=COLOR_WHITE, highlightthickness=1, highlightbackground=COLOR_BORDER)
        bp_canvas_f.pack(fill="both", expand=True)

        self.bp_canvas = tk.Canvas(bp_canvas_f, bg=COLOR_WHITE, highlightthickness=0)
        bp_scroll_y = ttk.Scrollbar(bp_canvas_f, orient="vertical", command=self.bp_canvas.yview)
        bp_scroll_x = ttk.Scrollbar(bp_canvas_f, orient="horizontal", command=self.bp_canvas.xview)
        self.bp_inner = tk.Frame(self.bp_canvas, bg=COLOR_WHITE)

        self.bp_inner.bind("<Configure>", lambda e: self.bp_canvas.configure(scrollregion=self.bp_canvas.bbox("all")))
        self.bp_canvas.create_window((0, 0), window=self.bp_inner, anchor="nw")
        self.bp_canvas.configure(xscrollcommand=bp_scroll_x.set, yscrollcommand=bp_scroll_y.set)

        self.bp_canvas.pack(side="top", fill="both", expand=True)
        bp_scroll_y.pack(side="right", fill="y")
        bp_scroll_x.pack(side="bottom", fill="x")

        try:
            self.hotel_map_photo = get_hotel_map_image((1200, 680))
            self.bp_img_label = tk.Label(self.bp_inner, image=self.hotel_map_photo, bg=COLOR_WHITE)
            self.bp_img_label.pack(padx=20, pady=20)
        except Exception as e:
            self.bp_img_label = tk.Label(self.bp_inner, text=f"Could not render HotelMap.jpg: {e}", fg=COLOR_DANGER, bg=COLOR_WHITE)
            self.bp_img_label.pack(padx=20, pady=40)

    def _set_view_mode(self, mode: str):
        self.current_view = mode
        if mode == "grid":
            self.blueprint_view_frame.pack_forget()
            self.grid_view_frame.pack(fill="both", expand=True)
            self.btn_grid_view.configure(bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", bd=0)
            self.btn_blueprint_view.configure(bg=COLOR_WHITE, fg=COLOR_PRIMARY, relief="solid", bd=1)
            self.refresh_rooms()
        else:
            self.grid_view_frame.pack_forget()
            self.blueprint_view_frame.pack(fill="both", expand=True)
            self.btn_blueprint_view.configure(bg=COLOR_PRIMARY, fg=COLOR_WHITE, relief="flat", bd=0)
            self.btn_grid_view.configure(bg=COLOR_WHITE, fg=COLOR_PRIMARY, relief="solid", bd=1)
            self._update_blueprint_kpis()

    def _update_blueprint_kpis(self):
        with self.get_connection() as conn:
            tot = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            occ = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Occupied'").fetchone()[0]
            vac = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Vacant'").fetchone()[0]
            svc = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Needs Service'").fetchone()[0]
            res = conn.execute("SELECT COUNT(*) FROM rooms WHERE status = 'Reserved'").fetchone()[0]

        txt = (
            f"Hotel Capacity: {tot} Rooms Total   •   "
            f"🔴 Occupied: {occ}   •   "
            f"🟢 Vacant: {vac}   •   "
            f"🟡 Needs Service: {svc}   •   "
            f"🔵 Reserved: {res}"
        )
        if hasattr(self, "bp_kpi_label"):
            self.bp_kpi_label.config(text=txt)

    def refresh_rooms(self):
        """Fetches latest rooms and reservations data from SQLite and renders floor cards."""
        for w in self.scroll_content.winfo_children():
            w.destroy()

        selected_filter = self.filter_var.get()

        with self.get_connection() as conn:
            # Query rooms along with checked-in customer name and overdue status
            query = """
                SELECT r.*,
                       res.id AS res_id, res.customer_id, res.check_in_date, res.check_out_date,
                       c.name AS guest_name, c.mobile_number, c.loyalty_points
                FROM rooms r
                LEFT JOIN reservations res ON r.id = res.room_id AND res.status = 'Checked In'
                LEFT JOIN customers c ON res.customer_id = c.id
                ORDER BY r.room_number ASC
            """
            rows = conn.execute(query).fetchall()

        # Group by floor levels (Floor 5 down to Floor 1)
        floors = {
            "Level 5 - Penthouse & Royal Suites": [],
            "Level 4 - Executive Suites": [],
            "Level 3 - Deluxe Balcony Rooms": [],
            "Level 2 - Deluxe Rooms": [],
            "Level 1 - Ground Level Rooms": []
        }

        for row in rows:
            r_num = str(row["room_number"])
            status = row["status"]

            # Filter logic
            if self.utilities_mode:
                # Utilities CANNOT see empty rooms (no one checked in)
                if status == "Vacant":
                    continue
                if selected_filter == "Occupied & Needs Service" and status not in {
                    "Occupied", "Needs Service"
                }:
                    continue
                if selected_filter == "Occupied" and status != "Occupied":
                    continue
                if selected_filter == "Needs Service" and status != "Needs Service":
                    continue
            else:
                if selected_filter != "All" and status != selected_filter:
                    continue

            if r_num.startswith("5"):
                floors["Level 5 - Penthouse & Royal Suites"].append(row)
            elif r_num.startswith("4"):
                floors["Level 4 - Executive Suites"].append(row)
            elif r_num.startswith("3"):
                floors["Level 3 - Deluxe Balcony Rooms"].append(row)
            elif r_num.startswith("2"):
                floors["Level 2 - Deluxe Rooms"].append(row)
            elif r_num.startswith("1"):
                floors["Level 1 - Ground Level Rooms"].append(row)

        rendered_count = 0
        for floor_title, room_list in floors.items():
            if not room_list:
                continue

            floor_card = tk.Frame(self.scroll_content, bg=COLOR_WHITE, padx=14, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
            floor_card.pack(fill="x", pady=6)

            # Floor header band
            f_head = tk.Frame(floor_card, bg=COLOR_WHITE)
            f_head.pack(fill="x", pady=(0, 8))

            tk.Label(
                f_head,
                text=floor_title,
                font=(FONT_FAMILY, 11, "bold"),
                fg=COLOR_PRIMARY,
                bg=COLOR_WHITE
            ).pack(side="left")

            count_str = f"{len(room_list)} room(s)"
            tk.Label(
                f_head,
                text=count_str,
                font=(FONT_FAMILY, 9),
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_WHITE
            ).pack(side="right")

            # Room items grid
            grid_frame = tk.Frame(floor_card, bg=COLOR_WHITE)
            grid_frame.pack(fill="x")

            col_max = 6
            for idx, r in enumerate(room_list):
                col = idx % col_max
                row_idx = idx // col_max

                self._render_room_box(grid_frame, r, row_idx, col)
                rendered_count += 1

        if rendered_count == 0:
            empty_box = tk.Frame(self.scroll_content, bg=COLOR_WHITE, padx=30, pady=40, highlightthickness=1, highlightbackground=COLOR_BORDER)
            empty_box.pack(fill="x", pady=20)
            tk.Label(
                empty_box,
                text="No rooms found matching the current filter criteria.",
                font=(FONT_FAMILY, 11, "italic"),
                fg=COLOR_TEXT_MUTED,
                bg=COLOR_WHITE
            ).pack()

    def _render_room_box(self, parent, room, r_idx, c_idx):
        status = room["status"]
        cfg = STATUS_COLORS.get(status, STATUS_COLORS["Vacant"])
        r_num = room["room_number"]
        guest = room["guest_name"] or "None"
        r_type = room["type"]
        price = room["price_per_night"]

        # Check overdue status
        is_overdue = False
        is_near_overdue = False
        if room["check_out_date"] and status == "Occupied":
            from datetime import date
            today_str = date.today().strftime("%Y-%m-%d")
            co_date = str(room["check_out_date"])
            if co_date < today_str:
                is_overdue = True
            elif co_date == today_str:
                is_near_overdue = True

        box_border = COLOR_DANGER if is_overdue else (COLOR_WARNING if is_near_overdue else cfg["border"])
        box = tk.Frame(
            parent,
            bg=cfg["bg"],
            highlightthickness=2,
            highlightbackground=box_border,
            padx=8,
            pady=8,
            cursor="hand2"
        )
        box.grid(row=r_idx, column=c_idx, padx=6, pady=6, sticky="nsew")
        parent.columnconfigure(c_idx, weight=1)

        # Header with Room Number and Status Tag
        h_frame = tk.Frame(box, bg=cfg["bg"])
        h_frame.pack(fill="x")

        tk.Label(
            h_frame,
            text=f"Room {r_num}",
            font=(FONT_FAMILY, 11, "bold"),
            fg=COLOR_TEXT_DARK,
            bg=cfg["bg"]
        ).pack(side="left")

        # Overdue alert tag or normal status
        if is_overdue:
            tag_text = "🚨 OVERDUE"
            tag_bg = COLOR_DANGER
            tag_fg = COLOR_WHITE
        elif is_near_overdue:
            tag_text = "⚠️ DUE TODAY"
            tag_bg = COLOR_WARNING
            tag_fg = COLOR_TEXT_DARK
        else:
            tag_text = status
            tag_bg = cfg["badge"]
            tag_fg = COLOR_WHITE

        tk.Label(
            h_frame,
            text=f" {tag_text} ",
            font=(FONT_FAMILY, 7, "bold"),
            bg=tag_bg,
            fg=tag_fg
        ).pack(side="right")

        # Type & Capacity
        tk.Label(
            box,
            text=r_type,
            font=(FONT_FAMILY, 8),
            fg=COLOR_TEXT_MUTED,
            bg=cfg["bg"]
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            box,
            text=f"PHP {price:,.0f} / night  •  {room['packs']} Packs",
            font=(FONT_FAMILY, 8, "bold"),
            fg=COLOR_PRIMARY,
            bg=cfg["bg"]
        ).pack(anchor="w")

        # Guest preview
        if status == "Occupied":
            guest_str = f"👤 {guest}"
            if len(guest_str) > 22:
                guest_str = guest_str[:20] + "..."
            tk.Label(
                box,
                text=guest_str,
                font=(FONT_FAMILY, 8, "bold"),
                fg=COLOR_DANGER_TEXT if not is_overdue else COLOR_DANGER,
                bg=cfg["bg"]
            ).pack(anchor="w", pady=(2, 0))
            if room["check_out_date"]:
                tk.Label(
                    box,
                    text=f"Out: {room['check_out_date']}",
                    font=(FONT_FAMILY, 7),
                    fg=COLOR_TEXT_MUTED,
                    bg=cfg["bg"]
                ).pack(anchor="w")
        elif status == "Reserved":
            tk.Label(
                box,
                text="📅 Upcoming Booking",
                font=(FONT_FAMILY, 8, "italic"),
                fg=COLOR_INFO_TEXT,
                bg=cfg["bg"]
            ).pack(anchor="w")
        elif status == "Needs Service":
            tk.Label(
                box,
                text="🧹 Service / Cleaning Pending",
                font=(FONT_FAMILY, 8, "bold"),
                fg=COLOR_WARNING_TEXT,
                bg=cfg["bg"]
            ).pack(anchor="w")

        # Click interaction
        def on_click(e, r=room):
            if self.on_room_click_cb:
                self.on_room_click_cb(r)
            else:
                self._show_default_room_modal(r)

        box.bind("<Button-1>", on_click)
        for child in box.winfo_children():
            child.bind("<Button-1>", on_click)
            for sub in child.winfo_children():
                sub.bind("<Button-1>", on_click)

    def _show_default_room_modal(self, room):
        """Displays informative modal with room status, guest details, and service actions."""
        r_num = room["room_number"]
        status = room["status"]
        guest = room["guest_name"] or "None"

        win = tk.Toplevel(self)
        win.title(f"Room {r_num} Details")
        win.geometry("450x420")
        win.configure(bg=COLOR_WHITE)
        win.transient(self)
        win.grab_set()

        header = tk.Frame(win, bg=COLOR_PRIMARY, padx=16, pady=12)
        header.pack(fill="x")

        tk.Label(header, text=f"ROOM {r_num} INSPECTION", font=(FONT_FAMILY, 14, "bold"), fg=COLOR_WHITE, bg=COLOR_PRIMARY).pack(side="left")
        tk.Label(header, text=f" {status} ", font=(FONT_FAMILY, 9, "bold"), bg=COLOR_ACCENT, fg=COLOR_TEXT_DARK).pack(side="right")

        content = tk.Frame(win, bg=COLOR_WHITE, padx=20, pady=16)
        content.pack(fill="both", expand=True)

        details = [
            ("Room Type", room["type"]),
            ("Rate Per Night", f"PHP {room['price_per_night']:,.2f}"),
            ("Capacity", f"{room['packs']} Guests"),
            ("Current Status", status),
            ("Current Guest", guest),
            ("Mobile Contact", room["mobile_number"] or "N/A"),
            ("Check-In Date", room["check_in_date"] or "N/A"),
            ("Check-Out Date", room["check_out_date"] or "N/A"),
        ]

        for idx, (label, val) in enumerate(details):
            row = tk.Frame(content, bg=COLOR_WHITE)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", font=(FONT_FAMILY, 9, "bold"), fg=COLOR_TEXT_MUTED, width=16, anchor="w", bg=COLOR_WHITE).pack(side="left")
            tk.Label(row, text=str(val), font=(FONT_FAMILY, 9), fg=COLOR_TEXT_DARK, bg=COLOR_WHITE).pack(side="left")

        # Action Buttons
        btn_frame = tk.Frame(win, bg=COLOR_WHITE, padx=20, pady=14)
        btn_frame.pack(fill="x")

        if status == "Needs Service":
            mark_btn = tk.Button(
                btn_frame,
                text="✓ Mark Service Completed (Vacant)",
                font=(FONT_FAMILY, 10, "bold"),
                bg=COLOR_SUCCESS,
                fg=COLOR_WHITE,
                relief="flat",
                command=lambda: self._update_room_status(win, room["id"], "Vacant")
            )
            mark_btn.pack(side="left", padx=4)
        elif status == "Vacant":
            req_btn = tk.Button(
                btn_frame,
                text="🧹 Request Room Service",
                font=(FONT_FAMILY, 10, "bold"),
                bg=COLOR_WARNING,
                fg=COLOR_TEXT_DARK,
                relief="flat",
                command=lambda: self._update_room_status(win, room["id"], "Needs Service")
            )
            req_btn.pack(side="left", padx=4)

        close_btn = tk.Button(
            btn_frame,
            text="Close",
            font=(FONT_FAMILY, 10),
            bg=COLOR_BG,
            fg=COLOR_TEXT_DARK,
            relief="flat",
            command=win.destroy
        )
        close_btn.pack(side="right")

    def _update_room_status(self, modal, room_id, new_status):
        with self.get_connection() as conn:
            conn.execute("UPDATE rooms SET status = ? WHERE id = ?", (new_status, room_id))
            conn.commit()
        modal.destroy()
        self.refresh_rooms()
        messagebox.showinfo("Status Updated", f"Room status updated to '{new_status}' successfully.")
