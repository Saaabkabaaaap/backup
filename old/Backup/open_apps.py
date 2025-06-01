import os
import subprocess
import platform

# 🛡️ Connect to Warp VPN
def connect_warp():
    try:
        print("Connecting Warp VPN...")
        # Run warp-cli connect command
        result = subprocess.run(["warp-cli", "connect"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Warp VPN connected successfully.")
        else:
            print("Failed to connect Warp VPN:")
            print(result.stderr)
    except Exception as e:
        print(f"Error connecting Warp VPN: {e}")


# 🖥️ Open applications
def open_app(app_path):
    try:
        if platform.system() == "Windows":
            os.startfile(app_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", app_path])
        elif platform.system() == "Linux":
            subprocess.Popen([app_path])
        else:
            print("Unsupported OS.")
    except Exception as e:
        print(f"Error opening {app_path}: {e}")

# ✅ Define your apps here
apps = {
    "1": r"C:\Program Files\Cloudflare\Cloudflare WARP\Cloudflare WARP.exe",
    "2": r"C:\Program Files\Ablaze Floorp\private_browsing.exe",
    "3": r"C:\Users\AMIT JAIN\AppData\Roaming\Telegram Desktop\Telegram.exe"
}
 
# 🖥️ Show menu
print("Select apps to open (e.g., 1 2 3):")
for key, path in apps.items():
    print(f"{key}: {os.path.basename(path)}")

# ⌨️ Get user input
choices = input("Enter numbers separated by space: ").split()

if "1" in choices:
    connect_warp()
# If Warp VPN is selected, connect to it

# 🚀 Open selected apps
for choice in choices:
    app_path = apps.get(choice)
    if app_path:
        open_app(app_path)
    else:
        print(f"Invalid choice: {choice}")
