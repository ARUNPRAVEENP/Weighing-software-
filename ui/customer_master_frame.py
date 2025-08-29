import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox

from Model.customer_model import Customer
from repositories.customer_repository import CustomerRepository
from viewmodels.master_viewmodel import CustomerMasterViewModel # Assuming this CustomerMasterViewModel works generically

class CustomerMasterFrame(ctk.CTkFrame):
    # CORRECTED: __init__ signature to accept all arguments being passed from MainDashboardWindow
    def __init__(self, master, user_permissions, customer_repository): 
        super().__init__(master)
        self.user_permissions = set(user_permissions or [])
        
        # CORRECTED: Use the passed customer_repository instance, don't create a new one
        self.repo = customer_repository 
        
        # Pass the correctly injected repository to the ViewModel
        self.vm = CustomerMasterViewModel(self.repo) 
        self.selected_customer_id = None

        self._build_ui()
        self._populate() # Call populate table on initialization to show data

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self)
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(outer, text="📇 Customer Master", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 15))

        form = ctk.CTkFrame(outer, fg_color="#F9FAFB", corner_radius=10)
        form.pack(fill="x", pady=(0, 15), padx=10)

        # Form Grid
        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(pady=10, padx=10)

        # Row 0
        ctk.CTkLabel(grid, text="📛 Name*", width=140, anchor="e").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")
        self.entry_name = ctk.CTkEntry(grid, width=260, placeholder_text="Customer name")
        self.entry_name.grid(row=0, column=1, pady=5)

        ctk.CTkLabel(grid, text="📞 Contact No", width=140, anchor="e").grid(row=0, column=2, padx=(20, 10), pady=5, sticky="e")
        self.entry_contact = ctk.CTkEntry(grid, width=260, placeholder_text="10-digit only")
        self.entry_contact.grid(row=0, column=3, pady=5)

    # Row 1
        ctk.CTkLabel(grid, text="📧 Email", width=140, anchor="e").grid(row=1, column=0, padx=(0, 10), pady=5, sticky="e")
        self.entry_email = ctk.CTkEntry(grid, width=260, placeholder_text="abc@email.com")
        self.entry_email.grid(row=1, column=1, pady=5)

        ctk.CTkLabel(grid, text="🏙️ City", width=140, anchor="e").grid(row=1, column=2, padx=(20, 10), pady=5, sticky="e")
        self.entry_city = ctk.CTkEntry(grid, width=260, placeholder_text="City name")
        self.entry_city.grid(row=1, column=3, pady=5)

    # Row 2
        ctk.CTkLabel(grid, text="📮 Pincode", width=140, anchor="e").grid(row=2, column=0, padx=(0, 10), pady=5, sticky="e")
        self.entry_pincode = ctk.CTkEntry(grid, width=260, placeholder_text="Optional")
        self.entry_pincode.grid(row=2, column=1, pady=5)

        ctk.CTkLabel(grid, text="🔢 GSTIN", width=140, anchor="e").grid(row=2, column=2, padx=(20, 10), pady=5, sticky="e")
        self.entry_gstin = ctk.CTkEntry(grid, width=260, placeholder_text="Optional")
        self.entry_gstin.grid(row=2, column=3, pady=5)

    # Row 3 (Address full width)
        ctk.CTkLabel(grid, text="📬 Address", width=140, anchor="e").grid(row=3, column=0, padx=(0, 10), pady=5, sticky="e")
        self.entry_address = ctk.CTkEntry(grid, width=600, placeholder_text="Optional address")
        self.entry_address.grid(row=3, column=1, columnspan=3, pady=5, sticky="w")

        # Buttons
        btn_row = ctk.CTkFrame(form, fg_color="transparent")
        btn_row.pack(pady=15, fill="x", padx=10)

        self.save_btn = ctk.CTkButton(btn_row, text="💾 Save", command=self._save)
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))
        # Use self.user_permissions for consistency
        if "CanAddCustomer" not in self.user_permissions:
            self.save_btn.configure(state="disabled")

        clear_btn = ctk.CTkButton(btn_row, text="❌ Clear", fg_color="#9CA3AF", command=self._clear)
        clear_btn.pack(side="left", expand=True, fill="x")

        self._build_table(outer)

    def _build_table(self, parent):
        wrapper = ctk.CTkFrame(parent, fg_color="#F0FDF4", corner_radius=12)
        wrapper.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        ctk.CTkLabel(wrapper, text="🧾 Registered Customers", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(15, 10))

        filter_row = tk.Frame(wrapper, bg="#F0FDF4")
        filter_row.pack(fill="x", padx=20, pady=(0, 10))

        self.filter_column = tk.StringVar(value="Name")
        ctk.CTkComboBox(filter_row, values=["Name", "City", "Contact", "GSTIN"], variable=self.filter_column, width=150).pack(side="left", padx=(0, 10))

        self.filter_entry = ctk.CTkEntry(filter_row, placeholder_text="Filter...")
        self.filter_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._populate())

        # Tree
        self.tree = ttk.Treeview(wrapper, columns=("Name", "Contact", "City", "GSTIN", "Actions"), show="headings", height=8)
        for col, width in zip(("Name", "Contact", "City", "GSTIN", "Actions"), (180, 120, 120, 160, 120)):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

        self.tree.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.tree.bind("<Button-1>", self._handle_action)
        # self._populate() # This will be called in __init__ now

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        q = self.filter_entry.get().strip().lower()
        col = self.filter_column.get()

        # Ensure vm.entities is refreshed or always up-to-date
        self.vm.load_entities() # Reload entities to ensure latest data from repo

        def match(c: Customer):
            val = ""
            if col == "Name":
                val = c.name or ""
            elif col == "City":
                val = c.city or ""
            elif col == "Contact":
                val = c.contact_number or ""
            elif col == "GSTIN":
                val = c.gst_id or ""
            return q in val.lower()

        for c in self.vm.entities:
            if q and not match(c): continue
            self.tree.insert("", "end", values=(
                c.name, c.contact_number or "-", c.city or "-", c.gst_id or "-", "📝 Edit      🗑️ Delete"
            ), iid=c.id) # Store the actual ID in the treeview item for easier lookup

    def _save(self):
        name = self.entry_name.get().strip().upper()
        contact = self.entry_contact.get().strip()
        email = self.entry_email.get().strip()
        city = self.entry_city.get().strip()
        pincode = self.entry_pincode.get().strip()
        gst = self.entry_gstin.get().strip()
        address = self.entry_address.get().strip()

        if not name:
            messagebox.showerror("Validation", "Customer name is required.")
            return
        if contact and (not contact.isdigit() or len(contact) != 10):
            messagebox.showerror("Validation", "Contact number must be a 10-digit number.")
            return
        if email and "@" not in email:
            messagebox.showerror("Validation", "Invalid email format.")
            return

        try:
            if self.selected_customer_id:
                # Use self.user_permissions for consistency
                if "CanEditCustomer" not in self.user_permissions:
                    messagebox.showwarning("Access Denied", "You don't have permission to edit customers.")
                    return
                self.vm.edit_entity(self.selected_customer_id, name, address, city, pincode, contact, email, gst)
                messagebox.showinfo("Updated", f"Customer '{name}' updated.")
            else:
                # Use self.user_permissions for consistency
                if "CanAddCustomer" not in self.user_permissions:
                    messagebox.showwarning("Access Denied", "You don't have permission to add customers.")
                    return
                self.vm.add_entity(name, address, city, pincode, contact, email, gst)
                messagebox.showinfo("Added", f"Customer '{name}' added.")

            self._clear()
        except ValueError as e:
            messagebox.showerror("Validation", str(e))
        except Exception as e: # Catch any other potential errors from viewmodel/repo
            messagebox.showerror("Operation Error", f"An error occurred: {e}")

    def _clear(self):
        self.entry_name.delete(0, tk.END)
        self.entry_contact.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_city.delete(0, tk.END)
        self.entry_pincode.delete(0, tk.END)
        self.entry_gstin.delete(0, tk.END)
        self.entry_address.delete(0, tk.END)

        self.selected_customer_id = None
        self.save_btn.configure(text="💾 Save")
        # Re-enable save button after clearing if permission allows
        if "CanAddCustomer" in self.user_permissions:
            self.save_btn.configure(state="normal")
        self.vm.load_entities() # Good to refresh VM here
        self._populate()

    def _handle_action(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return

        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id or col != "#5": return  # Actions column is #5 (index 4)

        # Get the actual customer ID stored in the iid
        customer_id = self.tree.item(row_id, "iid")
        cust = next((c for c in self.vm.entities if c.id == customer_id), None)
        if not cust:
            messagebox.showerror("Error", "Selected customer not found in data.")
            return

        bbox = self.tree.bbox(row_id, column=4) # Column index 4 for "Actions"
        if not bbox: return # In case bbox is None

        click_x = event.x - bbox[0]

        # Split cell into buttons
        edit_area_width = bbox[2] * 0.5 # First half for Edit

        if click_x < edit_area_width:
            # 📝 Edit
            self._edit(cust)
        else:
            # 🗑️ Delete
            self._delete(cust)

    def _edit(self, customer):
        self.selected_customer_id = customer.id
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, customer.name or "")

        self.entry_contact.delete(0, tk.END)
        self.entry_contact.insert(0, customer.contact_number or "")

        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, customer.email or "")

        self.entry_city.delete(0, tk.END)
        self.entry_city.insert(0, customer.city or "")

        self.entry_pincode.delete(0, tk.END)
        self.entry_pincode.insert(0, customer.pincode or "")

        self.entry_gstin.delete(0, tk.END)
        self.entry_gstin.insert(0, customer.gst_id or "")

        self.entry_address.delete(0, tk.END)
        self.entry_address.insert(0, customer.address or "")

        self.save_btn.configure(text="✅ Update")
        # Disable add if editing, unless user has both add/edit
        if "CanEditCustomer" in self.user_permissions:
             self.save_btn.configure(state="normal") # Keep enabled for update
        else:
             self.save_btn.configure(state="disabled") # Disable if only add permission


    def _delete(self, customer):
        # Use self.user_permissions for consistency
        if "CanDeleteCustomer" not in self.user_permissions:
            messagebox.showwarning("Access Denied", "You don’t have permission to delete customers.")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete customer '{customer.name}'?")
        if confirm:
            try:
                self.vm.delete_entity(customer.id)
                self._populate()
                messagebox.showinfo("Deleted", f"Customer '{customer.name}' removed.")
            except Exception as e:
                messagebox.showerror("Deletion Error", f"Failed to delete customer: {e}")