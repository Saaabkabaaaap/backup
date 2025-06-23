import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, font
import json
import subprocess
import os
import sys
import threading

# Optional system tray support
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None

APPS_FILE = "apps.json"
FAVORITES_FILE = "favorites.json"

def load_apps():
    try:
        with open(APPS_FILE, "r") as f:
            apps = json.load(f)
            # Validate apps format
            return [app for app in apps if isinstance(app, list) and len(app) == 2]
    except:
        return []

def save_apps(apps):
    with open(APPS_FILE, "w") as f:
        json.dump(apps, f, indent=2)

def load_favorites():
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_favorites(favorites):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f, indent=2)

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("App Launcher")
        self.root.geometry("720x560")

        # Fonts for nicer UI
        self.font_normal = font.Font(family="Segoe UI", size=11)
        self.font_bold = font.Font(family="Segoe UI", size=11, weight="bold")

        style = ttk.Style()
        style.configure("Treeview", font=self.font_normal)
        style.configure("Treeview.Heading", font=self.font_bold)

        self.apps = load_apps()
        self.favorites = load_favorites()

        # Dict to track checked state by app name
        self.checked_apps = {name: False for name, _ in self.apps}

        # Search bar frame
        search_frame = tk.Frame(root)
        search_frame.pack(fill='x', padx=10, pady=6)
        tk.Label(search_frame, text="Search:", font=self.font_bold).pack(side='left')
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search)
        tk.Entry(search_frame, textvariable=self.search_var, font=self.font_normal).pack(side='left', fill='x', expand=True)

        # Treeview for apps (with checkbox symbols)
        self.tree = ttk.Treeview(root, show='tree', selectmode='extended', height=17)
        self.tree.pack(fill='both', expand=True, padx=10)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_release)
        self.tree.bind("<B1-Motion>", self.on_tree_drag)

        self.checked_symbol = "☑ "
        self.unchecked_symbol = "☐ "

        # Buttons frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill='x', padx=10, pady=4)
        tk.Button(btn_frame, text="Add App", command=self.add_app, font=self.font_bold).pack(side='left')
        tk.Button(btn_frame, text="Edit App", command=self.edit_app, font=self.font_bold).pack(side='left', padx=6)
        tk.Button(btn_frame, text="Delete App", command=self.delete_app, font=self.font_bold).pack(side='left')
        tk.Button(btn_frame, text="Launch Selected", command=self.launch_selected_apps, font=self.font_bold).pack(side='right')

        # Favorites label and listbox
        tk.Label(root, text="Favorites:", font=self.font_bold).pack(anchor='w', padx=10, pady=(10, 0))
        fav_frame = tk.Frame(root)
        fav_frame.pack(fill='x', padx=10)

        self.fav_listbox = tk.Listbox(fav_frame, height=6, font=self.font_normal)
        self.fav_listbox.pack(side='left', fill='x', expand=True)
        self.fav_listbox.bind("<Double-1>", self.on_fav_double_click)

        fav_btn_frame = tk.Frame(fav_frame)
        fav_btn_frame.pack(side='left', padx=8)
        tk.Button(fav_btn_frame, text="Add Favorite", command=self.add_favorite, font=self.font_bold).pack(fill='x')
        tk.Button(fav_btn_frame, text="Delete Favorite", command=self.delete_favorite, font=self.font_bold).pack(fill='x', pady=4)
        tk.Button(fav_btn_frame, text="Launch Favorite", command=self.launch_favorite, font=self.font_bold).pack(fill='x')

        self.dragging_item = None
        self.filtered_apps = []

        # Load apps into treeview
        self.refresh_favorites()
        self.on_search()

        # Setup system tray icon if pystray is available
        self.icon = None
        if pystray:
            self.setup_system_tray()

        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

    # ========== Treeview / App list methods ==========

    def refresh_tree(self):
        # Preserve selections and checked states
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())

        search_text = self.search_var.get().lower()
        self.filtered_apps = [app for app in self.apps if search_text in app[0].lower()]

        for name, path in self.filtered_apps:
            checked = self.checked_apps.get(name, False)
            symbol = self.checked_symbol if checked else self.unchecked_symbol
            self.tree.insert("", "end", iid=name, text=symbol + name)

        # Restore selection if possible
        to_select = [iid for iid in selected if iid in [a[0] for a in self.filtered_apps]]
        if to_select:
            self.tree.selection_set(to_select)

    def on_search(self, *args):
        self.refresh_tree()

    def on_tree_click(self, event):
        # Identify item and toggle checkbox if clicked near left
        region = self.tree.identify("region", event.x, event.y)
        if region != "tree":
            return

        iid = self.tree.identify_row(event.y)
        if not iid:
            return

        # Toggle checkbox if clicked within first 20 pixels of tree item
        if event.x < 20:
            self.checked_apps[iid] = not self.checked_apps.get(iid, False)
            symbol = self.checked_symbol if self.checked_apps[iid] else self.unchecked_symbol
            self.tree.item(iid, text=symbol + iid)
        else:
            # Start dragging for reorder
            self.dragging_item = iid

    def on_tree_double_click(self, event):
        # Launch double-clicked app
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        app = next((a for a in self.apps if a[0] == iid), None)
        if app:
            self.launch_apps([app])

    def on_tree_drag(self, event):
        if not self.dragging_item:
            return
        y = event.y
        target_iid = self.tree.identify_row(y)
        if not target_iid or target_iid == self.dragging_item:
            return

        # Get current indexes in apps list
        names = [a[0] for a in self.apps]
        try:
            drag_idx = names.index(self.dragging_item)
            target_idx = names.index(target_iid)
        except ValueError:
            return

        # Reorder apps list
        app = self.apps.pop(drag_idx)
        self.apps.insert(target_idx, app)

        save_apps(self.apps)
        self.refresh_tree()
        self.tree.selection_set(self.dragging_item)

    def on_tree_release(self, event):
        self.dragging_item = None

    # ========== App management ==========

    def add_app(self):
        name = simpledialog.askstring("Add App", "Enter app name:", parent=self.root)
        if not name:
            return
        if any(name == app[0] for app in self.apps):
            messagebox.showerror("Error", "App name already exists.", parent=self.root)
            return
        path = filedialog.askopenfilename(title="Select app executable or file")
        if not path:
            return
        self.apps.append([name, path])
        self.checked_apps[name] = False
        save_apps(self.apps)
        self.refresh_tree()

    def edit_app(self):
        sel = self.tree.selection()
        if len(sel) != 1:
            messagebox.showerror("Error", "Select exactly one app to edit.", parent=self.root)
            return
        old_name = sel[0]
        app = next((a for a in self.apps if a[0] == old_name), None)
        if not app:
            return
        new_name = simpledialog.askstring("Edit App", "Edit app name:", initialvalue=app[0], parent=self.root)
        if not new_name:
            return
        if new_name != old_name and any(new_name == a[0] for a in self.apps):
            messagebox.showerror("Error", "App name already exists.", parent=self.root)
            return
        new_path = filedialog.askopenfilename(title="Select app executable or file", initialdir=os.path.dirname(app[1]))
        if not new_path:
            new_path = app[1]

        # Update
        for i, a in enumerate(self.apps):
            if a[0] == old_name:
                self.apps[i] = [new_name, new_path]
                break
        # Update checked_apps dict key if name changed
        if new_name != old_name:
            checked = self.checked_apps.pop(old_name, False)
            self.checked_apps[new_name] = checked
        save_apps(self.apps)
        self.refresh_tree()

    def delete_app(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select app(s) to delete.", parent=self.root)
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(sel)} app(s)?", parent=self.root):
            return
        self.apps = [a for a in self.apps if a[0] not in sel]
        for name in sel:
            self.checked_apps.pop(name, None)
        save_apps(self.apps)
        self.refresh_tree()

    # ========== Launching apps ==========

    def launch_apps(self, apps_to_launch):
        for name, path in apps_to_launch:
            if not os.path.exists(path):
                messagebox.showerror("Error", f"Path not found:\n{path}", parent=self.root)
                continue
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                else:
                    subprocess.Popen([path])

                # Special Warp VPN handling
                if name.lower() == "warp":
                    self.root.after(2000, self.connect_warp_cli)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch {name}:\n{e}", parent=self.root)

    def connect_warp_cli(self):
        try:
            subprocess.run(["warp-cli", "connect"], check=True)
            print("Warp VPN connected")
        except Exception as e:
            messagebox.showerror("Warp VPN Error", f"Failed to connect Warp VPN:\n{e}", parent=self.root)

    def launch_selected_apps(self):
        to_launch = [app for app in self.apps if self.checked_apps.get(app[0], False)]
        if not to_launch:
            messagebox.showinfo("Info", "No apps selected to launch.", parent=self.root)
            return
        self.launch_apps(to_launch)

    # ========== Favorites ==========

    def refresh_favorites(self):
        self.fav_listbox.delete(0, tk.END)
        for fav in self.favorites:
            self.fav_listbox.insert(tk.END, fav)

    def add_favorite(self):
        fav_name = simpledialog.askstring("Add Favorite", "Enter favorite name:", parent=self.root)
        if not fav_name:
            return
        if fav_name in self.favorites:
            messagebox.showerror("Error", "Favorite already exists.", parent=self.root)
            return
        selected = [name for name, _ in self.apps if self.checked_apps.get(name, False)]
        if not selected:
            messagebox.showerror("Error", "Select at least one app to add to favorite.", parent=self.root)
            return
        self.favorites[fav_name] = selected
        save_favorites(self.favorites)
        self.refresh_favorites()

    def delete_favorite(self):
        sel = self.fav_listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "Select a favorite to delete.", parent=self.root)
            return
        fav_name = self.fav_listbox.get(sel[0])
        if not messagebox.askyesno("Confirm Delete", f"Delete favorite '{fav_name}'?", parent=self.root):
            return
        self.favorites.pop(fav_name, None)
        save_favorites(self.favorites)
        self.refresh_favorites()

    def launch_favorite_by_name(self, fav_name):
        if fav_name not in self.favorites:
            messagebox.showerror("Error", f"Favorite '{fav_name}' not found.", parent=self.root)
            return
        app_names = self.favorites[fav_name]
        apps_to_launch = [app for app in self.apps if app[0] in app_names]
        if not apps_to_launch:
            messagebox.showinfo("Info", "No apps to launch in this favorite.", parent=self.root)
            return
        self.launch_apps(apps_to_launch)

    def launch_favorite(self):
        sel = self.fav_listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "Select a favorite to launch.", parent=self.root)
            return
        fav_name = self.fav_listbox.get(sel[0])
        self.launch_favorite_by_name(fav_name)

    def on_fav_double_click(self, event):
        sel = self.fav_listbox.curselection()
        if sel:
            fav_name = self.fav_listbox.get(sel[0])
            self.launch_favorite_by_name(fav_name)

    # ========== System tray ==========

    def setup_system_tray(self):
        # Create icon image (simple blue square with white rectangle)
        image = Image.new("RGB", (64, 64), "blue")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 24, 48, 40), fill="white")

        menu = pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Quit", self.quit_app)
        )

        self.icon = pystray.Icon("app_launcher", image, "App Launcher", menu=menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def minimize_to_tray(self):
        if self.icon:
            self.root.withdraw()
        else:
            self.root.iconify()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()
