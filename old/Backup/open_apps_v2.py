import os
import subprocess
import platform

# --- CONFIGURABLE DATA (put this at the top!) ---

apps = {
    "1": r"notepad.exe",
    "2": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "3": r"C:\Windows\System32\calc.exe",
    "4": "warp"  # Warp VPN special
}

batches = {
    "a": ["1", "2", "3"],      # Batch A: Notepad, Chrome, Calculator
    "b": ["4", "2"],           # Batch B: Warp VPN and Chrome
    # Add more batches here
}

# --- FUNCTIONS ---

def connect_warp():
    try:
        print("Connecting Warp VPN...")
        result = subprocess.run(["warp-cli", "connect"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Warp VPN connected successfully.")
        else:
            print("Failed to connect Warp VPN:")
            print(result.stderr)
    except Exception as e:
        print(f"Error connecting Warp VPN: {e}")

def open_app(app_path):
    try:
        print(f"Opening: {app_path}")
        if platform.system() == "Windows":
            os.startfile(app_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", app_path])
        else:
            subprocess.run(["xdg-open", app_path])
    except Exception as e:
        print(f"Failed to open {app_path}: {e}")

def open_apps_from_list(app_keys):
    if "4" in app_keys:
        connect_warp()
        app_keys = [k for k in app_keys if k != "4"]
    
    for app_key in app_keys:
        app_path = apps.get(app_key)
        if app_path:
            open_app(app_path)
        else:
            print(f"Invalid app key: {app_key}")

# --- USER INTERFACE ---

print("Single apps:")
for key, path in apps.items():
    name = "Warp VPN" if path == "warp" else os.path.basename(path)
    print(f"  {key}: {name}")

print("\nBatch options:")
for key, batch_apps in batches.items():
    batch_names = [("Warp VPN" if apps[a] == "warp" else os.path.basename(apps[a])) for a in batch_apps]
    print(f"  {key}: Opens {', '.join(batch_names)}")

choices = input("\nEnter your selections (e.g. 1 a 2): ").split()

# --- PROCESS CHOICES ---

final_app_keys = []

for choice in choices:
    if choice in apps:
        final_app_keys.append(choice)
    elif choice in batches:
        final_app_keys.extend(batches[choice])
    else:
        print(f"Invalid choice: {choice}")

# Remove duplicates while keeping order
final_app_keys = list(dict.fromkeys(final_app_keys))

# --- LAUNCH ---

open_apps_from_list(final_app_keys)
