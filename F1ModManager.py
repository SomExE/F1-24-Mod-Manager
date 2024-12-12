import os
import zipfile
import shutil
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import py7zr

class F1ModManager:
    CONFIG_FILE = "config.json"
    ACTIVE_MODS_FILE = "active_mods.json"

    def __init__(self):
        self._load_config()
        self._ensure_backup_exists()
        self.active_mods = self._load_active_mods()

    def _load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as file:
                config = json.load(file)
                self.game_folder = config.get("game_folder", "")
                self.backup_folder = config.get("backup_folder", "")
                self.mods_folder = config.get("mods_folder", "")
        else:
            self._setup_config()

    def _load_active_mods(self):
        if os.path.exists(self.ACTIVE_MODS_FILE):
            with open(self.ACTIVE_MODS_FILE, "r") as file:
                return json.load(file)
        return []

    def _save_active_mods(self, active_mods):
        with open(self.ACTIVE_MODS_FILE, "w") as file:
            json.dump(active_mods, file, indent=4)

    def _setup_config(self):
        self.game_folder = filedialog.askdirectory(title="Select the game folder")
        self.backup_folder = filedialog.askdirectory(title="Select the backup folder")
        self.mods_folder = filedialog.askdirectory(title="Select the mods folder")

        config = {
            "game_folder": self.game_folder,
            "backup_folder": self.backup_folder,
            "mods_folder": self.mods_folder
        }
        with open(self.CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)

    def edit_config(self):
        self._setup_config()

    def _ensure_backup_exists(self):
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)

            for root, _, files in os.walk(self.game_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.game_folder)
                    backup_path = os.path.join(self.backup_folder, relative_path)

                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(file_path, backup_path)

    def _get_mod_folder(self, mod_archive):
        mod_folder = os.path.join(self.mods_folder, os.path.splitext(os.path.basename(mod_archive))[0])
        if not os.path.exists(mod_folder):
            if mod_archive.endswith('.zip'):
                with zipfile.ZipFile(mod_archive, 'r') as zip_ref:
                    zip_ref.extractall(mod_folder)
            elif mod_archive.endswith('.7z'):
                with py7zr.SevenZipFile(mod_archive, mode='r') as archive:
                    archive.extractall(mod_folder)
        return mod_folder

    def activate_mod(self, mod_archive):
        mod_name = os.path.basename(mod_archive)
        mod_folder = self._get_mod_folder(mod_archive)
        mod_game_folder = os.path.join(mod_folder, 'F1 24')

        for root, _, files in os.walk(mod_game_folder):
            for file in files:
                mod_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(mod_file_path, mod_game_folder)
                game_file_path = os.path.join(self.game_folder, relative_path)

                if os.path.exists(game_file_path):
                    backup_path = os.path.join(self.backup_folder, relative_path)
                    if not os.path.exists(backup_path):
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        shutil.copy2(game_file_path, backup_path)

                os.makedirs(os.path.dirname(game_file_path), exist_ok=True)
                shutil.copy2(mod_file_path, game_file_path)

        # Add mod to active mods list and save
        if mod_name not in self.active_mods:
            self.active_mods.append(mod_name)
            self._save_active_mods(self.active_mods)

    def deactivate_mod(self, mod_archive):
        mod_name = os.path.basename(mod_archive)
        mod_folder = self._get_mod_folder(mod_archive)
        mod_game_folder = os.path.join(mod_folder, 'F1 24')

        for root, _, files in os.walk(mod_game_folder):
            for file in files:
                mod_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(mod_file_path, mod_game_folder)
                game_file_path = os.path.join(self.game_folder, relative_path)
                backup_path = os.path.join(self.backup_folder, relative_path)

                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, game_file_path)
                elif os.path.exists(game_file_path):
                    os.remove(game_file_path)

        # Remove mod from active mods list and save
        if mod_name in self.active_mods:
            self.active_mods.remove(mod_name)
            self._save_active_mods(self.active_mods)

    def list_mods(self):
        return [f for f in os.listdir(self.mods_folder) if f.endswith(('.zip', '.7z'))]

class F1ModManagerApp:
    def __init__(self, root):
        self.manager = F1ModManager()
        self.root = root
        self.root.title("F1 Mod Manager")

        # Set dark mode
        self.root.tk_setPalette(background="#2e2e2e", foreground="#ffffff", activeBackground="#444444", activeForeground="#ffffff")

        self.active_mods = self.manager.active_mods
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
        style.configure("TButton", background="#444444", foreground="#ffffff")
        style.configure("TFrame", background="#2e2e2e")

        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=("N", "W", "E", "S"))

        ttk.Label(frame, text="Game Folder:").grid(row=0, column=0, sticky="e")
        self.game_folder_entry = ttk.Entry(frame, width=50)
        self.game_folder_entry.insert(0, self.manager.game_folder)
        self.game_folder_entry.grid(row=0, column=1)
        ttk.Button(frame, text="Browse", command=self.browse_game_folder).grid(row=0, column=2)

        ttk.Label(frame, text="Backup Folder:").grid(row=1, column=0, sticky="e")
        self.backup_folder_entry = ttk.Entry(frame, width=50)
        self.backup_folder_entry.insert(0, self.manager.backup_folder)
        self.backup_folder_entry.grid(row=1, column=1)
        ttk.Button(frame, text="Browse", command=self.browse_backup_folder).grid(row=1, column=2)

        ttk.Label(frame, text="Mods Folder:").grid(row=2, column=0, sticky="e")
        self.mods_folder_entry = ttk.Entry(frame, width=50)
        self.mods_folder_entry.insert(0, self.manager.mods_folder)
        self.mods_folder_entry.grid(row=2, column=1)
        ttk.Button(frame, text="Browse", command=self.browse_mods_folder).grid(row=2, column=2)

        ttk.Button(frame, text="Save Config", command=self.save_config).grid(row=3, column=0, columnspan=3, pady=5)

        ttk.Label(frame, text="Available Mods:").grid(row=4, column=0)
        ttk.Label(frame, text="Active Mods:").grid(row=4, column=2)

        self.available_mods_listbox = tk.Listbox(frame, width=40, height=10, selectmode="browse", bg="#444444", fg="#ffffff", selectbackground="#555555", selectforeground="#ffffff")
        self.available_mods_listbox.grid(row=5, column=0)

        self.active_mods_listbox = tk.Listbox(frame, width=40, height=10, selectmode="browse", bg="#444444", fg="#ffffff", selectbackground="#555555", selectforeground="#ffffff")
        self.active_mods_listbox.grid(row=5, column=2)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=5, column=1, pady=10)
        ttk.Button(button_frame, text="Activate Mod >>", command=self.activate_mod).grid(row=0, column=0, pady=5)
        ttk.Button(button_frame, text="<< Deactivate Mod", command=self.deactivate_mod).grid(row=1, column=0, pady=5)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_mods_list).grid(row=2, column=0, pady=5)

        self.refresh_mods_list()
        self.auto_reactivate_mods()

    def browse_game_folder(self):
        self.manager.game_folder = filedialog.askdirectory(title="Select the game folder")
        self.game_folder_entry.delete(0, tk.END)
        self.game_folder_entry.insert(0, self.manager.game_folder)

    def browse_backup_folder(self):
        self.manager.backup_folder = filedialog.askdirectory(title="Select the backup folder")
        self.backup_folder_entry.delete(0, tk.END)
        self.backup_folder_entry.insert(0, self.manager.backup_folder)

    def browse_mods_folder(self):
        self.manager.mods_folder = filedialog.askdirectory(title="Select the mods folder")
        self.mods_folder_entry.delete(0, tk.END)
        self.mods_folder_entry.insert(0, self.manager.mods_folder)

    def save_config(self):
        self.manager.game_folder = self.game_folder_entry.get()
        self.manager.backup_folder = self.backup_folder_entry.get()
        self.manager.mods_folder = self.mods_folder_entry.get()
        self.manager._setup_config()
        messagebox.showinfo("Config Saved", "Configuration saved successfully!")

    def refresh_mods_list(self):
        self.available_mods_listbox.delete(0, tk.END)
        self.active_mods_listbox.delete(0, tk.END)

        available_mods = self.manager.list_mods()
        for mod in available_mods:
            if mod not in self.active_mods:
                self.available_mods_listbox.insert(tk.END, mod)
            else:
                self.active_mods_listbox.insert(tk.END, mod)

    def auto_reactivate_mods(self):
        """Automatically reactivate mods that were active in the previous session"""
        for mod in self.active_mods:
            try:
                mod_path = os.path.join(self.manager.mods_folder, mod)
                self.manager.activate_mod(mod_path)
            except Exception as e:
                messagebox.showwarning("Mod Reactivation Error", f"Could not reactivate {mod}: {str(e)}")

    def activate_mod(self):
        try:
            selected_mod = self.available_mods_listbox.get(tk.ACTIVE)
            if selected_mod:
                full_path = os.path.join(self.manager.mods_folder, selected_mod)
                self.manager.activate_mod(full_path)
                self.active_mods = self.manager.active_mods
                self.refresh_mods_list()
                messagebox.showinfo("Mod Activated", f"{selected_mod} activated successfully!")
            else:
                raise ValueError("No mod selected.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def deactivate_mod(self):
        try:
            selected_mod = self.active_mods_listbox.get(tk.ACTIVE)
            if selected_mod:
                full_path = os.path.join(self.manager.mods_folder, selected_mod)
                self.manager.deactivate_mod(full_path)
                self.active_mods = self.manager.active_mods
                self.refresh_mods_list()
                messagebox.showinfo("Mod Deactivated", f"{selected_mod} deactivated successfully!")
            else:
                raise ValueError("No mod selected.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = F1ModManagerApp(root)
    root.mainloop()