import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure these imports are correct based on your project structure
# The repository should be instantiated once in the main app and passed in
from repositories.vehicle_repository import VehicleRepository 
from Model.vehicle_type_model import VehicleType # Assuming VehicleType model class is needed here
from viewmodels.master_viewmodel import VehicleMasterViewModel

class VehicleTypeFrame(ctk.CTkFrame):
    # CORRECTED: __init__ signature to accept all arguments being passed from MainDashboardWindow
    def __init__(self, master, user_permissions, vehicle_repository): 
        super().__init__(master)
        # Renamed 'current_permissions' to 'user_permissions' for consistency with MainDashboardWindow
        self.user_permissions = set(user_permissions or []) 
        
        # CORRECTED: Use the passed vehicle_repository instance, don't create a new one
        self.repo = vehicle_repository 
        
        # Pass the correctly injected repository to the ViewModel
        self.vm = VehicleMasterViewModel(self.repo) 
        self.selected_vehicle_id = None

        self.entry_name = None
        self.entry_tare = None
        self.entry_capacity = None

        self._build_ui()
        self._populate_table() # Call populate table on initialization to show data

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="🚛 Vehicle Type Master", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 10))

    # 🚧 Form Section
        form_frame = ctk.CTkFrame(scroll, fg_color="#F4F4F5", corner_radius=10)
        form_frame.pack(fill="x", padx=10, pady=(0, 15))

    # Vehicle Name
        name_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_row.pack(pady=5, anchor="w")
        ctk.CTkLabel(name_row, text="🚛 Vehicle Type:", width=150, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_name = ctk.CTkEntry(name_row, width=280, placeholder_text="Enter vehicle type name")
        self.entry_name.grid(row=0, column=1)

    # Tare Weight
        tare_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        tare_row.pack(pady=5, anchor="w")
        ctk.CTkLabel(tare_row, text="⚖️ Default Tare (kg):", width=150, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_tare = ctk.CTkEntry(tare_row, width=280, placeholder_text="Optional")
        self.entry_tare.grid(row=0, column=1)

    # Max Capacity
        capacity_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        capacity_row.pack(pady=5, anchor="w")
        ctk.CTkLabel(capacity_row, text="📦 Max Capacity (kg):", width=150, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_capacity = ctk.CTkEntry(capacity_row, width=280, placeholder_text="Optional")
        self.entry_capacity.grid(row=0, column=1)

    # Button Row
        btn_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_row.pack(pady=15, padx=10, fill="x")

        self.save_button = ctk.CTkButton(btn_row, text="💾 Save", command=self._save_vehicle)
        self.save_button.pack(side="left", expand=True, padx=(0, 10), fill="x")
        # Use self.user_permissions for consistency
        if "CanAddVehicle" not in self.user_permissions: 
            self.save_button.configure(state="disabled")

        clear_btn = ctk.CTkButton(btn_row, text="❌ Clear", fg_color="#9CA3AF", command=self._clear_fields)
        clear_btn.pack(side="left", expand=True, fill="x")

        self._build_table(scroll)
    
    def _build_table(self, parent):
        table_frame = ctk.CTkFrame(parent, fg_color="#ECFDF5", corner_radius=12)
        table_frame.pack(fill="both", padx=10, pady=(0, 10), expand=True)

        ctk.CTkLabel(
            table_frame,
            text="📋 Registered Vehicle Types",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))

        tree_wrap = tk.Frame(table_frame, bg="#ECFDF5")
        tree_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 🔍 Unified Filter Row
        filter_frame = tk.Frame(tree_wrap, bg="#ECFDF5")
        filter_frame.pack(fill="x", pady=(0, 10))

        # Column Selector
        self.filter_column = tk.StringVar(value="Vehicle Type")
        column_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Vehicle Type", "Default Tare", "Max Capacity"],
            variable=self.filter_column,
            width=140
        )
        column_combo.pack(side="left", padx=(10, 8))
        column_combo.bind("<<ComboboxSelected>>", lambda _: self._populate_table())

        # Filter Mode Selector
        self.filter_mode = tk.StringVar(value="Contains")
        mode_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Contains", "Starts with", "Equals"],
            variable=self.filter_mode,
            width=120
        )
        mode_combo.pack(side="left", padx=(0, 10))
        mode_combo.bind("<<ComboboxSelected>>", lambda _: self._populate_table())

        # Shared Search Entry
        self.search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(filter_frame, textvariable=self.search_var, width=240, placeholder_text="Enter filter text")
        search_entry.pack(side="left", padx=(0, 10))
        search_entry.bind("<KeyRelease>", lambda _: self._populate_table())

        # Incomplete Checkbox
        self.incomplete_only = tk.BooleanVar(value=False)
        incomplete_check = ctk.CTkCheckBox(
            filter_frame,
            text="⚠️ Incomplete Only",
            variable=self.incomplete_only,
            command=self._populate_table
        )
        incomplete_check.pack(side="left", padx=(10, 0))

        # Treeview
        self.tree = ttk.Treeview(tree_wrap, columns=("Name", "Tare", "Capacity", "Actions"), show="headings", height=8)
        self.tree.heading("Name", text="Vehicle Type")
        self.tree.heading("Tare", text="Default Tare (kg)")
        self.tree.heading("Capacity", text="Max Capacity (kg)")
        self.tree.heading("Actions", text="Actions")

        self.tree.column("Name", anchor="center", width=200)
        self.tree.column("Tare", anchor="center", width=150)
        self.tree.column("Capacity", anchor="center", width=180)
        self.tree.column("Actions", anchor="center", width=140)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 12), rowheight=34)
        style.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"))

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self._handle_action_click)
        # self._populate_table() # This will be called in __init__ now
    
    def _save_vehicle(self):
        name = self.entry_name.get().strip().upper()
        tare = self.entry_tare.get().strip()
        capacity = self.entry_capacity.get().strip()

        if not name:
            messagebox.showerror("Missing Info", "Vehicle type name is required.")
            return

        try:
            tare = float(tare) if tare else None
            capacity = float(capacity) if capacity else None
        except ValueError:
            messagebox.showerror("Input Error", "Tare or capacity must be numeric.")
            return

        try:
            if self.selected_vehicle_id:
                # Use self.user_permissions for consistency
                if "CanEditVehicle" not in self.user_permissions: 
                    messagebox.showwarning("Access Denied", "You don't have permission to edit vehicles.")
                    return
                self.vm.edit_entity(self.selected_vehicle_id, name, tare, capacity)
                messagebox.showinfo("Updated", f"Vehicle '{name}' updated.")
            else:
                # Use self.user_permissions for consistency
                if "CanAddVehicle" not in self.user_permissions: 
                    messagebox.showwarning("Access Denied", "You don't have permission to add vehicles.")
                    return
                self.vm.add_entity(name, tare, capacity)
                messagebox.showinfo("Success", f"Vehicle '{name}' added.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        self._clear_fields()
        self._populate_table()

    def _clear_fields(self):
        self.entry_name.delete(0, "end")
        self.entry_tare.delete(0, "end")
        self.entry_capacity.delete(0, "end")
        self.selected_vehicle_id = None
        self.save_button.configure(text="💾 Save")
        # Re-enable save button after clearing if permission allows
        if "CanAddVehicle" in self.user_permissions:
            self.save_button.configure(state="normal")


    def _populate_table(self):
        self.tree.delete(*self.tree.get_children())

        column = self.filter_column.get()
        mode = self.filter_mode.get()
        query = self.search_var.get().strip().upper()
        show_incomplete = self.incomplete_only.get()

        def matches(value):
            value = str(value or "").upper()
            if not query:
                return True
            if mode == "Contains":
                return query in value
            elif mode == "Starts with":
                return value.startswith(query)
            elif mode == "Equals":
                return value == query
            return True

        # Ensure vm.entities is refreshed or always up-to-date
        self.vm.load_entities() # Reload entities to ensure latest data from repo

        for v in self.vm.entities:
            name = v.name or ""
            tare = v.default_tare_weight
            cap = v.max_weight_capacity

        # Select column based on user choice
            if column == "Vehicle Type" and not matches(name):
                continue
            elif column == "Default Tare" and not matches(tare):
                continue
            elif column == "Max Capacity" and not matches(cap):
                continue

            if show_incomplete and (tare is not None and cap is not None):
                continue # Skip if complete and 'show_incomplete' is true

            self.tree.insert("", "end", values=(
            name,
            tare if tare is not None else "-",
            cap if cap is not None else "-",
            "📝 Edit      🗑️ Delete" # Maintain consistent spacing for button overlay logic
            ), iid=v.id) # Store the actual ID in the treeview item for easier lookup
    
    def _handle_action_click(self, event):
        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not row_id or col != "#4": # Check if it's the 4th column (Actions)
            return  # Clicked outside the Actions column

        # Get the actual vehicle ID stored in the iid
        vehicle_id = self.tree.item(row_id, "iid")
        vehicle = next((v for v in self.vm.entities if v.id == vehicle_id), None)

        if not vehicle:
            messagebox.showerror("Error", "Selected vehicle not found in data.")
            return

        bbox = self.tree.bbox(row_id, column="Actions")
        if not bbox: return # In case bbox is None

        click_x = event.x - bbox[0]

        # Calculate approximate click areas for "Edit" and "Delete"
        edit_area_width = bbox[2] * 0.5 # First half for Edit
        # delete_area_width = bbox[2] * 0.5 # Second half for Delete

        if click_x < edit_area_width:
        # 📝 Edit
            if "CanEditVehicle" in self.user_permissions:
                self._load_vehicle_for_edit(vehicle)
            else:
                messagebox.showwarning("Access Denied", "You don't have permission to edit vehicles.")
        else:
        # 🗑️ Delete
            if "CanDeleteVehicle" not in self.user_permissions:
                messagebox.showwarning("Access Denied", "You don't have permission to delete vehicles.")
                return

            confirm = messagebox.askyesno("Confirm Deletion", f"Delete vehicle '{vehicle.name}'?")
            if confirm:
                try:
                    self.vm.delete_entity(vehicle.id)
                    self._populate_table()
                    messagebox.showinfo("Deleted", f"Vehicle '{vehicle.name}' removed.")
                except Exception as e:
                    messagebox.showerror("Deletion Error", f"Failed to delete vehicle: {e}")

    def _load_vehicle_for_edit(self, vehicle):
        self.selected_vehicle_id = vehicle.id
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, vehicle.name)
        self.entry_tare.delete(0, "end")
        if vehicle.default_tare_weight is not None:
            self.entry_tare.insert(0, str(vehicle.default_tare_weight))
        self.entry_capacity.delete(0, "end")
        if vehicle.max_weight_capacity is not None:
            self.entry_capacity.insert(0, str(vehicle.max_weight_capacity))
        self.save_button.configure(text="✅ Update")
        # Disable add if editing, unless user has both add/edit
        if "CanAddVehicle" in self.user_permissions:
             self.save_button.configure(state="normal") # Keep enabled for update
        else:
             self.save_button.configure(state="disabled") # Disable if only add permission