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
                data = json.load(f)
                if isinstance(data, dict):
                    return list(data.items())
                return data
        except json.JSONDecodeError:
            return list(default_apps().items())
    else:
        return list(default_apps().items())

def save_apps(apps_list):
    with open(APP_FILE, "w") as f:
        json.dump(dict(apps_list), f, indent=2)

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

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("App Launcher")

        self.apps = load_apps()
        self.favorites = load_favorites()

        self.create_widgets()
        self.refresh_app_list()
        self.update_fav_menu()

        self.dragging_index = None
        self.current_hover_index = None

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=5, fill='both', expand=True)

        self.listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, activestyle='none', exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill='both', expand=True)
        self.listbox.bind('<ButtonPress-1>', self.on_drag_start)
        self.listbox.bind('<B1-Motion>', self.on_drag_motion)
        self.listbox.bind('<ButtonRelease-1>', self.on_drag_drop)
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_change)
        self.listbox.bind('<Motion>', self.on_mouse_motion)

        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Arrow buttons fixed on the right side, small and side by side
        self.arrow_frame = tk.Frame(frame)
        self.arrow_frame.pack(side=tk.LEFT, fill='y', padx=5)

        self.up_btn = tk.Button(self.arrow_frame, text='↑', width=2, height=1, command=self.move_selected_up)
        self.down_btn = tk.Button(self.arrow_frame, text='↓', width=2, height=1, command=self.move_selected_down)
        self.up_btn.grid(row=0, column=0, padx=1, pady=2)
        self.down_btn.grid(row=0, column=1, padx=1, pady=2)

        # Initially disable buttons if no apps or only one app
        if len(self.apps) <= 1:
            self.up_btn.config(state=tk.DISABLED)
            self.down_btn.config(state=tk.DISABLED)

        # Buttons below list
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Launch Selected", command=self.launch_selected).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Save as Favorite", command=self.save_favorite).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected App(s)", command=self.delete_selected_apps).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Edit Selected App", command=self.edit_selected_app).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Add New App", command=self.toggle_add_section).grid(row=0, column=4, padx=5)

        fav_frame = tk.Frame(self.root)
        fav_frame.pack(pady=5, fill='x')

        tk.Label(fav_frame, text="Favorites:").pack(side=tk.LEFT, padx=(5,0))
        self.fav_var = tk.StringVar()
        self.fav_menu = ttk.Combobox(fav_frame, textvariable=self.fav_var, values=list(self.favorites.keys()), state="readonly")
        self.fav_menu.pack(side=tk.LEFT, padx=5, fill='x', expand=True)
        self.fav_menu.bind("<<ComboboxSelected>>", self.load_selected_favorite)

        self.delete_fav_btn = tk.Button(fav_frame, text="Delete Favorite", command=self.delete_favorite)
        self.delete_fav_btn.pack(side=tk.LEFT, padx=5)

        self.add_section_visible = False
        self.add_inputs_frame = tk.Frame(self.root)

        tk.Label(self.add_inputs_frame, text="App Name:").grid(row=0, column=0, sticky='w')
        self.app_name_entry = tk.Entry(self.add_inputs_frame)
        self.app_name_entry.grid(row=0, column=1, sticky='ew')

        tk.Label(self.add_inputs_frame, text="App Path:").grid(row=1, column=0, sticky='w')
        self.app_path_entry = tk.Entry(self.add_inputs_frame)
        self.app_path_entry.grid(row=1, column=1, sticky='ew')

        self.add_inputs_frame.columnconfigure(1, weight=1)

        self.add_button = tk.Button(self.add_inputs_frame, text="Add", command=self.add_app)
        self.add_button.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')

    # Drag and drop handlers
    def on_drag_start(self, event):
        self.dragging_index = self.listbox.nearest(event.y)

    def on_drag_motion(self, event):
        if self.dragging_index is None:
            return
        new_index = self.listbox.nearest(event.y)
        if new_index != self.dragging_index:
            self.apps.insert(new_index, self.apps.pop(self.dragging_index))
            self.dragging_index = new_index
            self.refresh_app_list()
            self.listbox.selection_set(new_index)

    def on_drag_drop(self, event):
        self.dragging_index = None
        self.save_apps_order()

    # Arrow buttons logic on mouse hover
    def on_mouse_motion(self, event):
        idx = self.listbox.nearest(event.y)
        self.current_hover_index = idx
        if idx == 0:
            self.up_btn.config(state=tk.DISABLED)
        else:
            self.up_btn.config(state=tk.NORMAL)

        if idx == len(self.apps) - 1:
            self.down_btn.config(state=tk.DISABLED)
        else:
            self.down_btn.config(state=tk.NORMAL)

    def on_selection_change(self, event):
        pass  # no action needed here

    def move_selected_up(self):
        idx = self.current_hover_index
        if idx is None or idx == 0:
            return
        self.apps[idx-1], self.apps[idx] = self.apps[idx], self.apps[idx-1]
        self.refresh_app_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx-1)
        self.listbox.see(idx-1)
        self.save_apps_order()

    def move_selected_down(self):
        idx = self.current_hover_index
        if idx is None or idx >= len(self.apps) - 1:
            return
        self.apps[idx], self.apps[idx+1] = self.apps[idx+1], self.apps[idx]
        self.refresh_app_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx+1)
        self.listbox.see(idx+1)
        self.save_apps_order()

    def refresh_app_list(self):
        self.listbox.delete(0, tk.END)
        for name, _ in self.apps:
            self.listbox.insert(tk.END, name)

    def save_apps_order(self):
        save_apps(self.apps)

    def launch_selected(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select at least one app to launch.")
            return
        for idx in selected_indices:
            name, path = self.apps[idx]
            if path == "warp":
                connect_warp()
            else:
                try:
                    os.startfile(path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open {name}: {e}")

    def save_favorite(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Nothing Selected", "Select at least one app to save as favorite.")
            return
        selected_names = [self.apps[i][0] for i in selected_indices]
        name = simpledialog.askstring("Save Favorite", "Enter a name for this favorite:")
        if name:
            self.favorites[name] = selected_names
            save_favorites(self.favorites)
            self.update_fav_menu()
            messagebox.showinfo("Saved", f"Favorite '{name}' saved!")

    def load_selected_favorite(self, event=None):
        name = self.fav_var.get()
        if name in self.favorites:
            self.listbox.selection_clear(0, tk.END)
            fav_apps = self.favorites[name]
            for i, (app_name, _) in enumerate(self.apps):
                if app_name in fav_apps:
                    self.listbox.selection_set(i)

    def update_fav_menu(self):
        self.fav_menu['values'] = list(self.favorites.keys())
        if self.favorites:
            self.fav_var.set(list(self.favorites.keys())[0])
        else:
            self.fav_var.set("")

    def delete_favorite(self):
        name = self.fav_var.get()
        if not name:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete favorite '{name}'?"):
            self.favorites.pop(name, None)
            save_favorites(self.favorites)
            self.update_fav_menu()

    def delete_selected_apps(self):
        selected_indices = list(self.listbox.curselection())
        if not selected_indices:
            messagebox.showinfo("No Selection", "Select app(s) to delete.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete selected {len(selected_indices)} app(s)?"):
            for idx in reversed(selected_indices):
                self.apps.pop(idx)
            self.refresh_app_list()
            self.save_apps_order()

    def edit_selected_app(self):
        selected_indices = self.listbox.curselection()
        if len(selected_indices) != 1:
            messagebox.showinfo("Select One", "Select exactly one app to edit.")
            return
        idx = selected_indices[0]
        old_name, old_path = self.apps[idx]
        new_name = simpledialog.askstring("Edit App Name", "App Name:", initialvalue=old_name)
        if new_name is None or new_name.strip() == "":
            return
        new_path = simpledialog.askstring("Edit App Path", "App Path:", initialvalue=old_path)
        if new_path is None or new_path.strip() == "":
            return
        self.apps[idx] = (new_name.strip(), new_path.strip())
        self.refresh_app_list()
        self.save_apps_order()

    def toggle_add_section(self):
        if self.add_section_visible:
            self.add_inputs_frame.pack_forget()
            self.add_section_visible = False
        else:
            self.add_inputs_frame.pack(fill='x', padx=10, pady=5)
            self.add_section_visible = True

    def add_app(self):
        name = self.app_name_entry.get().strip()
        path = self.app_path_entry.get().strip()
        if not name or not path:
            messagebox.showwarning("Invalid Input", "App name and path cannot be empty.")
            return
        self.apps.append((name, path))
        self.refresh_app_list()
        self.save_apps_order()
        self.app_name_entry.delete(0, tk.END)
        self.app_path_entry.delete(0, tk.END)
        self.toggle_add_section()

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()
