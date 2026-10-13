
import tkinter as tk
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from database.db import initialize_database
from Login import LoginPage
from Register import RegisterPage


class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("The Quest Company - Hotel Management")
        self.geometry("1920x1080")
        self.minsize(900, 600)

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    def show_login(self):
        self.clear_page()
        page = LoginPage(
            self.container,
            show_register=self.show_register
        )
        page.pack(fill="both", expand=True)

    def show_register(self):
        self.clear_page()
        page = RegisterPage(
            self.container,
            show_login=self.show_login
        )
        page.pack(fill="both", expand=True)

    def clear_page(self):
        for widget in self.container.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    initialize_database()

    app = HotelApp()
    app.mainloop()
