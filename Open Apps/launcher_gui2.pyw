import os
import json
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk

APP_FILE = os.path.join(os.path.dirname(__file__), "apps.json")
FAV_FILE = os.path.join(os.path.dirname(__file__), "favorites.json")

def default_apps():
    return {
        "Notepad": r"notepad.exe",
        "Chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "Calculator": r"C:\Windows\System32\calc.exe",
        "Warp VPN": "warp"
    }

def load_apps():
    if os.path.exists(APP_FILE):
        try:
            with open(APP_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default_apps()
    else:
        return default_apps()

def save_apps(apps_data):
    with open(APP_FILE, "w") as f:
        json.dump(apps_data, f, indent=2)

def load_favorites():
    if os.path.exists(FAV_FILE):
        try:
            with open(FAV_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_favorites(data):
    with open(FAV_FILE, "w") as f:
        json.dump(data, f, indent=2)

def connect_warp():
    try:
        os.system("warp-cli connect")
        print("Warp VPN launched")
    except Exception as e:
        print(f"Failed to connect Warp VPN: {e}")

apps = load_apps()
favorites = load_favorites()

root = tk.Tk()
root.title("App Launcher")

checkboxes = {}

app_frame = tk.Frame(root)
app_frame.pack(pady=5)

def refresh_checkboxes():
    for widget in app_frame.winfo_children():
        widget.destroy()
    checkboxes.clear()
    for app_name in apps:
        var = tk.BooleanVar()
        cb = tk.Checkbutton(app_frame, text=app_name, variable=var)
        cb.pack(anchor='w')
        checkboxes[app_name] = var

refresh_checkboxes()

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

tk.Button(root, text="Launch Selected", command=launch_selected).pack(pady=5)

def save_favorite():
    selected = [name for name, var in checkboxes.items() if var.get()]
    if not selected:
        messagebox.showinfo("Nothing Selected", "Select at least one app to save.")
        return
    name = simpledialog.askstring("Save Favorite", "Enter a name for this favorite:")
    if name:
        favorites[name] = selected
        save_favorites(favorites)
        update_fav_menu()
        messagebox.showinfo("Saved", f"Favorite '{name}' saved!")

tk.Button(root, text="Save as Favorite", command=save_favorite).pack(pady=5)

fav_var = tk.StringVar()
fav_menu = ttk.Combobox(root, textvariable=fav_var, values=list(favorites.keys()), state="readonly")
fav_menu.pack(pady=5)

def load_selected_favorite(event=None):
    name = fav_var.get()
    if name in favorites:
        for key in checkboxes:
            checkboxes[key].set(False)
        for app in favorites[name]:
            if app in checkboxes:
                checkboxes[app].set(True)

fav_menu.bind("<<ComboboxSelected>>", load_selected_favorite)

def update_fav_menu():
    fav_menu['values'] = list(favorites.keys())

update_fav_menu()
if favorites:
    fav_var.set(list(favorites.keys())[0])
    load_selected_favorite()

# --- Toggle Add App Section ---

add_section_visible = False

def toggle_add_section():
    global add_section_visible
    if add_section_visible:
        add_inputs_frame.pack_forget()
        add_section_visible = False
    else:
        add_inputs_frame.pack(pady=5, fill='x')
        add_section_visible = True

toggle_button = tk.Button(root, text="Add New App", command=toggle_add_section)
toggle_button.pack(pady=10)

# Hidden Add App Section
add_inputs_frame = tk.Frame(root)

tk.Label(add_inputs_frame, text="App Name:").grid(row=0, column=0, sticky='w')
app_name_entry = tk.Entry(add_inputs_frame)
app_name_entry.grid(row=0, column=1, sticky='ew')

tk.Label(add_inputs_frame, text="App Path:").grid(row=1, column=0, sticky='w')
app_path_entry = tk.Entry(add_inputs_frame)
app_path_entry.grid(row=1, column=1, sticky='ew')

add_inputs_frame.columnconfigure(1, weight=1)

def add_app():
    name = app_name_entry.get().strip()
    path = app_path_entry.get().strip()
    if not name or not path:
        messagebox.showwarning("Input Error", "Both App Name and Path are required.")
        return
    if name in apps:
        messagebox.showwarning("Duplicate", "App name already exists.")
        return
    apps[name] = path
    save_apps(apps)
    refresh_checkboxes()
    app_name_entry.delete(0, tk.END)
    app_path_entry.delete(0, tk.END)
    toggle_add_section()

add_button = tk.Button(add_inputs_frame, text="Add", command=add_app)
add_button.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')

root.mainloop()
