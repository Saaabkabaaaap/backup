import os
import tkinter as tk
from tkinter import messagebox

# Define the apps and their paths
apps = {
    "Notepad": r"notepad.exe",
    "Chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "Calculator": r"C:\Windows\System32\calc.exe",
    "Warp VPN": "warp"  # special case
}

# Function to connect Warp VPN
def connect_warp():
    try:
        result = os.system("warp-cli connect")
        print("Warp VPN launched")
    except Exception as e:
        print(f"Failed to connect Warp VPN: {e}")

# Function to launch selected apps
def launch_selected():
    for app_name, var in checkboxes.items():
        if var.get():
            path = apps[app_name]
            if path == "warp":
                connect_warp()
            else:
                try:
                    os.startfile(path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open {app_name}: {e}")

# GUI setup
root = tk.Tk()
root.title("App Launcher")

# Store checkboxes
checkboxes = {}

# Create checkboxes
for app_name in apps:
    var = tk.BooleanVar()
    cb = tk.Checkbutton(root, text=app_name, variable=var)
    cb.pack(anchor='w')
    checkboxes[app_name] = var

# Launch button
launch_button = tk.Button(root, text="Launch Selected", command=launch_selected)
launch_button.pack(pady=10)

root.mainloop()
