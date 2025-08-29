import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

from Model.material_type_model import MaterialType
from repositories.material_repository import MaterialRepository
from viewmodels.master_viewmodel import MasterViewModel # Assuming this MasterViewModel works generically with different repositories

class MaterialTypeFrame(ctk.CTkFrame):
    # CORRECTED: __init__ signature to accept all arguments being passed from MainDashboardWindow
    def __init__(self, master, user_permissions, material_repository): 
        super().__init__(master)
        # Renamed 'current_permissions' to 'user_permissions' for consistency with MainDashboardWindow
        self.user_permissions = set(user_permissions or []) 
        
        # CORRECTED: Use the passed material_repository instance, don't create a new one
        self.repo = material_repository 
        
        # Pass the correctly injected repository to the ViewModel
        self.vm = MasterViewModel(self.repo) 
        self.selected_material_id = None

        self._build_ui()
        self._populate() # Call populate table on initialization to show data

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="📦 Material Master", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 10))

        # 🧾 Form
        form = ctk.CTkFrame(scroll, fg_color="#F4F4F5", corner_radius=10)
        form.pack(fill="x", padx=10, pady=(0, 15))

        # Name
        name_row = ctk.CTkFrame(form, fg_color="transparent")
        name_row.pack(pady=5, anchor="w")
        ctk.CTkLabel(name_row, text="📄 Material Name:", width=150, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_name = ctk.CTkEntry(name_row, width=280, placeholder_text="Enter material name")
        self.entry_name.grid(row=0, column=1)

        # Charges
        charges_row = ctk.CTkFrame(form, fg_color="transparent")
        charges_row.pack(pady=5, anchor="w")
        ctk.CTkLabel(charges_row, text="💰 Charges (₹):", width=150, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_charges = ctk.CTkEntry(charges_row, width=280, placeholder_text="Optional")
        self.entry_charges.grid(row=0, column=1)

        # Unit
        unit_row = ctk.CTkFrame(form, fg_color="transparent")
        unit_row.pack(pady=5, anchor="w")
        ctk.CTkLabel(unit_row, text="📏 Unit of Measure:", width=150, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.unit_var = tk.StringVar()
        unit_combo = ctk.CTkComboBox(unit_row, values=["KG", "TON", "BAG", "LITRE"], variable=self.unit_var, width=280)
        unit_combo.grid(row=0, column=1)

        # Buttons
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(pady=15, padx=10, fill="x")

        self.save_btn = ctk.CTkButton(btn_row, text="💾 Save", command=self._save)
        self.save_btn.pack(side="left", expand=True, padx=(0, 10), fill="x")
        # Use self.user_permissions for consistency
        if "CanAddMaterial" not in self.user_permissions:
            self.save_btn.configure(state="disabled")

        clear_btn = ctk.CTkButton(btn_row, text="❌ Clear", fg_color="#9CA3AF", command=self._clear)
        clear_btn.pack(side="left", expand=True, fill="x")

        self._build_table(scroll)

    def _build_table(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="#ECFDF5", corner_radius=12)
        frame.pack(fill="both", padx=10, pady=(0, 10), expand=True)

        ctk.CTkLabel(frame, text="📋 Registered Materials", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        table_wrap = tk.Frame(frame, bg="#ECFDF5")
        table_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Filters
        filter_row = tk.Frame(table_wrap, bg="#ECFDF5")
        filter_row.pack(fill="x", pady=(0, 10))

        self.filter_column = tk.StringVar(value="Material Name")
        column_combo = ctk.CTkComboBox(filter_row, values=["Material Name", "Charges", "Unit"], variable=self.filter_column, width=160)
        column_combo.pack(side="left", padx=(10, 6))
        column_combo.bind("<<ComboboxSelected>>", lambda e: self._populate())

        self.filter_mode = tk.StringVar(value="Contains")
        mode_combo = ctk.CTkComboBox(filter_row, values=["Contains", "Starts with", "Equals"], variable=self.filter_mode, width=120)
        mode_combo.pack(side="left", padx=(0, 10))
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self._populate())

        self.search_var = tk.StringVar()
        search_box = ctk.CTkEntry(filter_row, textvariable=self.search_var, width=240, placeholder_text="Filter...")
        search_box.pack(side="left")
        search_box.bind("<KeyRelease>", lambda e: self._populate())

        self.incomplete_only = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(filter_row, text="⚠️ Incomplete Only", variable=self.incomplete_only, command=self._populate).pack(side="left", padx=(10, 0))

        # Treeview
        self.tree = ttk.Treeview(table_wrap, columns=("Name", "Charges", "Unit", "Actions"), show="headings", height=8)
        self.tree.heading("Name", text="Material Name")
        self.tree.heading("Charges", text="Charges (₹)")
        self.tree.heading("Unit", text="Unit")
        self.tree.heading("Actions", text="Actions")

        self.tree.column("Name", anchor="center", width=220)
        self.tree.column("Charges", anchor="center", width=130)
        self.tree.column("Unit", anchor="center", width=130)
        self.tree.column("Actions", anchor="center", width=140)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 12), rowheight=34)
        style.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"))

        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self._handle_action)
        # self._populate() # This will be called in __init__ now

    def _populate(self):
        self.tree.delete(*self.tree.get_children())

        col = self.filter_column.get()
        mode = self.filter_mode.get()
        query = self.search_var.get().strip().upper()
        incomplete = self.incomplete_only.get()

        def matches(val):
            val = str(val or "").upper()
            if not query:
                return True
            if mode == "Contains":
                return query in val
            elif mode == "Starts with":
                return val.startswith(query)
            elif mode == "Equals":
                return val == query
            return True

        # --- MODIFIED LINE ---
        self.vm.refresh() # Reload entities using the refresh method
        # --- END MODIFIED LINE ---

        for m in self.vm.entities:
            if col == "Material Name" and not matches(m.name):
                continue
            elif col == "Charges" and not matches(m.charges):
                continue
            elif col == "Unit" and not matches(m.unit):
                continue
            
            # Logic for incomplete: only show if charges OR unit is None/empty
            if incomplete and (m.charges is not None and m.unit): # If both are present, it's NOT incomplete
                continue # Skip if complete and 'show_incomplete' is true

            self.tree.insert("", "end", values=(
                m.name,
                m.charges if m.charges is not None else "-",
                m.unit or "-",
                "📝 Edit      🗑️ Delete" # Maintain consistent spacing for button overlay logic
            ), iid=m.id) # Store the actual ID in the treeview item for easier lookup

    def _save(self):
        print("✅ Save button was clicked.")
        name = self.entry_name.get().strip().upper()
        charges = self.entry_charges.get().strip()
        unit = self.unit_var.get().strip() or None

        if not name:
            messagebox.showerror("Missing Info", "Material name is required.")
            return
        if charges and not unit:
            messagebox.showerror("Missing Unit", "Unit is required when charges are provided.")
            return

        try:
            charges = float(charges) if charges else None
        except ValueError:
            messagebox.showerror("Input Error", "Charges must be numeric.")
            return

        try: # Added try-except for overall save operation
            if self.selected_material_id:
                # Use self.user_permissions for consistency
                if "CanEditMaterial" not in self.user_permissions:
                    messagebox.showwarning("Access Denied", "You don't have permission to edit materials.")
                    return

                self.vm.edit_entity(self.selected_material_id, name, charges, unit)
                messagebox.showinfo("Updated", f"Material '{name}' updated successfully.")
            else:
                # Use self.user_permissions for consistency
                if "CanAddMaterial" not in self.user_permissions:
                    messagebox.showwarning("Access Denied", "You don't have permission to add materials.")
                    return

                self.vm.add_entity(name, charges, unit)
                messagebox.showinfo("Added", f"Material '{name}' added successfully.")
        except Exception as e: # Catch potential errors from viewmodel/repo
            messagebox.showerror("Operation Error", f"An error occurred: {e}")


        self._clear()

    
    def _clear(self):
        self.entry_name.delete(0, tk.END)
        self.entry_charges.delete(0, tk.END)
        self.unit_var.set("")
        self.selected_material_id = None
        self.save_btn.configure(text="💾 Save")
        # Re-enable save button after clearing if permission allows
        if "CanAddMaterial" in self.user_permissions:
            self.save_btn.configure(state="normal")
        self.vm.refresh() # Good to refresh VM here
        self._populate()

    def _handle_action(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id or col != "#4": # Check if it's the 4th column (Actions)
            return

        # Get the actual material ID stored in the iid
        material_id = self.tree.item(row_id, "iid")
        material = next((m for m in self.vm.entities if m.id == material_id), None)
        if not material:
            messagebox.showerror("Error", "Selected material not found in data.")
            return

        bbox = self.tree.bbox(row_id, column=3)
        if not bbox: return # In case bbox is None

        click_x = event.x - bbox[0]

        # Split cell into buttons
        edit_area_width = bbox[2] * 0.5 # First half for Edit

        if click_x < edit_area_width:
            # 📝 Edit
            self._edit(material)
        else:
            # 🗑️ Delete
            self._delete(material)

    def _edit(self, material):
        self.selected_material_id = material.id
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, material.name)

        self.entry_charges.delete(0, tk.END)
        if material.charges is not None:
            self.entry_charges.insert(0, str(material.charges))

        self.unit_var.set(material.unit or "")
        self.save_btn.configure(text="✅ Update")
        # Disable add if editing, unless user has both add/edit
        if "CanEditMaterial" in self.user_permissions:
             self.save_btn.configure(state="normal") # Keep enabled for update
        else:
             self.save_btn.configure(state="disabled") # Disable if only add permission

    def _delete(self, material):
        # Use self.user_permissions for consistency
        if "CanDeleteMaterial" not in self.user_permissions:
            messagebox.showwarning("Access Denied", "You don’t have permission to delete materials.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Delete material '{material.name}'?")
        if confirm:
            try:
                self.vm.delete_entity(material.id)
                self._populate()
                messagebox.showinfo("Deleted", f"Material '{material.name}' removed.")
            except Exception as e:
                messagebox.showerror("Deletion Error", f"Failed to delete material: {e}")

