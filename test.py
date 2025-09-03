import sys
import tkinter as tk
try:
    import pyperclip
    pyperclip_status = "SUCCESS: pyperclip is installed."
except ImportError:
    pyperclip_status = "ERROR: pyperclip is not installed."

# Print crucial information to the terminal
print("=== PYTHON ENVIRONMENT CHECK ===")
print(f"Python Executable Path: {sys.executable}")
print(f"Pyperclip Status: {pyperclip_status}")
print("===============================")

# Test a simple GUI
root = tk.Tk()
root.title("Environment Test")
root.geometry("400x200")

label_text = f"""If you can see this window, tkinter works!

Python Path:
{sys.executable}

Pyperclip:
{pyperclip_status}
"""

label = tk.Label(root, text=label_text, justify=tk.LEFT, font=("Consolas", 10))
label.pack(padx=20, pady=20)

root.mainloop()