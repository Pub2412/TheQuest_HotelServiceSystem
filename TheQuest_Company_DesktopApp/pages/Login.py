import tkinter as tk

# Main Window
root = tk.Tk()

# Set the title of the window
root.title("Login Page")

# Set the size of the window
root.geometry("1920x1080")

label = tk.Label(root, text="Welcome to The Quest Company")
label.place(x = 110, y = 40)

button_login = tk.Button(root, text="Login", command=lambda: print("Login button clicked"))
button_login.place(x = 110, y = 80)

# Start the main event loop
root.mainloop()
