import tkinter as tk

# Create the main application window
root = tk.Tk()

# Set the title of the window
root.title("My Tkinter Application")

# Set the size of the window
root.geometry("300x200")

label = tk.Label(root, text="Hello, World!")
label.place(x = 100, y = 40)

button = tk.Button(root, text="Click Me!", command=lambda: label.config(text="Button Clicked!"))
button.place(x = 110, y = 80)

# Start the GUI event loop
root.mainloop()