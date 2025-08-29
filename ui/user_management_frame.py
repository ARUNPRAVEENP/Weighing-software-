import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from viewmodels.user_management_viewmodel import UserManagementViewModel
from repositories.user_repository import UserRepository

class UserManagementFrame(ctk.CTkFrame):
    def __init__(self, master, current_user, current_permissions):
        super().__init__(master)
        self.current_user = current_user
        self.current_permissions = set(current_permissions)
        self.user_repo = UserRepository()
        self.vm = UserManagementViewModel(self.user_repo)
        self.selected_user_id = None
        self.permission_vars = {}

        self.permission_groups = {
            "Vehicle Management": ["CanViewVehicle","CanAddVehicle","CanEditVehicle","CanDeleteVehicle"],
            "User Management": ["CanAddUser", "CanEditUser", "CanDeleteUser", "CanManageUserPermissions"],
            "Customer Access": ["CanAddCustomer", "CanEditCustomer", "CanDeleteCustomer"],
            "Material Control": ["CanAddMaterial", "CanEditMaterial", "CanDeleteMaterial"],
            "Weighing": ["CanWeighEntry", "CanOverrideWeight", "CanEditWeighTransaction", "CanDeleteWeighTransaction", "CanPrintWeighSlip", "CanApplyWeighCharges"],
            "Reports": ["CanViewReports", "CanExportReports"]
        }

        # 🖼️ Scrollable wrapper
        self.scroll_area = ctk.CTkScrollableFrame(self)
        self.scroll_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.build_ui(self.scroll_area)
    
    def build_ui(self, parent):
        title = ctk.CTkLabel(parent, text="👤 User Management", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(10, 5))

        user_id_card = ctk.CTkFrame(parent, fg_color="#DBEAFE", corner_radius=8)
        user_id_card.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(user_id_card, text="🔐 Your User ID:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(6, 0))
        ctk.CTkLabel(user_id_card, text=self.current_user, font=("Arial", 13), text_color="#1E3A8A").pack(anchor="w", padx=10, pady=(0, 8))

        self.form_frame = ctk.CTkFrame(parent, fg_color="#F4F4F5", corner_radius=10)
        self.form_frame.pack(fill="x", padx=10, pady=(0, 10))
        self._build_form_section()

        self._build_user_table(parent)
    from tkinter import ttk
    style = ttk.Style()
    style.configure("Treeview", font=("Segoe UI", 13))              # Cell font
    style.configure("Treeview.Heading", font=("Segoe UI", 14, "bold"))  # Header font
    style.configure("Treeview", rowheight=32)                        # Row height for spacing

    def _build_user_table(self, parent):
        box = ctk.CTkFrame(parent, fg_color="#ECFDF5", corner_radius=8)
        box.pack(fill="both", padx=10, pady=(10, 20), expand=True)

        ctk.CTkLabel(box, text="📋 Managed Users", font=("Arial", 18, "bold")).pack(anchor="w", padx=10, pady=10)
        tree_frame = tk.Frame(box)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.user_list = ttk.Treeview(
            tree_frame,
            columns=("Username", "Permissions", "Actions"),
            show="headings",
            height=8
        )
        self.user_list.heading("Username", text="Username")
        self.user_list.heading("Permissions", text="Permissions")
        self.user_list.heading("Actions", text="Actions")

        self.user_list.column("Username", anchor="center", width=150)
        self.user_list.column("Permissions", anchor="center", width=550)
        self.user_list.column("Actions", anchor="center", width=160)

        self.user_list.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=self.user_list.yview)
        self.user_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.user_list.bind("<Button-1>", self._handle_action_click)
        self._populate_user_list()
    
    def _populate_user_list(self):
        self.user_list.delete(*self.user_list.get_children())
        for uname in self.user_repo.get_all_username():
            perms = self.vm.get_permissions_for_user(uname)
            self.user_list.insert("", "end", values=(uname, ", ".join(perms), "📝 Edit    🗑️ Delete"))
    
    def _handle_action_click(self, event):
        row_id = self.user_list.identify_row(event.y)
        col = self.user_list.identify_column(event.x)

        if not row_id or col != "#3":
            return

        values = self.user_list.item(row_id, "values")
        uname = values[0]
        user_id = self.vm.get_user_id_by_username(uname)
        if not user_id:
            messagebox.showerror("Error", "User ID not found.")
            return

        cell_bbox = self.user_list.bbox(row_id, column="Actions")
        click_x = event.x - cell_bbox[0]

        if click_x < cell_bbox[2] // 2:
            if "CanEditUser" in self.current_permissions:
                self._open_edit_user_popup(uname)
            else:
                messagebox.showwarning("Access Denied", "You do not have permission to edit users.")
        else:
            if "CanDeleteUser" not in self.current_permissions:
                messagebox.showwarning("Access Denied", "You do not have permission to delete users.")
                return
            confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete user '{uname}'?")
            if confirm:
                self.vm.delete_user_by_id(user_id)
                self._populate_user_list()
    
    def _load_user_for_edit(self, username):
        self.selected_user_id = self.vm.get_user_id_by_username(username)
        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, username)
        self.entry_password.delete(0, "end")
        perms = self.vm.get_permissions_for_user(username)
        for name, var in self.permission_vars.items():
            var.set(name in perms)
      
    def _build_form_section(self):
        ctk.CTkLabel(self.form_frame, text="🧾 Add New User", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(15, 8))

        username_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        username_row.pack(pady=5)
        ctk.CTkLabel(username_row, text="👤 Username:", width=120, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_username = ctk.CTkEntry(username_row, width=300, placeholder_text="Enter username")
        self.entry_username.grid(row=0, column=1)

        password_row = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        password_row.pack(pady=5)
        ctk.CTkLabel(password_row, text="🔒 Password:", width=120, anchor="e", font=ctk.CTkFont(size=14)).grid(row=0, column=0, padx=(0, 10))
        self.entry_password = ctk.CTkEntry(password_row, width=300, placeholder_text="Enter password", show="*")
        self.entry_password.grid(row=0, column=1)

        ctk.CTkLabel(self.form_frame, text="🔐 Permissions", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(15, 5))

        permission_frame = ctk.CTkScrollableFrame(self.form_frame, height=220)
        permission_frame.pack(fill="x", padx=20, pady=(0, 10))

        for group, perms in self.permission_groups.items():
            group_label = ctk.CTkLabel(permission_frame, text=group, font=ctk.CTkFont(weight="bold", size=15))
            group_label.pack(anchor="w", pady=(10, 2), padx=10)
            checkbox_row = ctk.CTkFrame(permission_frame, fg_color="transparent")
            checkbox_row.pack(anchor="w", padx=20)
            for i, perm in enumerate(perms):
                var = tk.BooleanVar()
                cb = ctk.CTkCheckBox(checkbox_row, text=perm, variable=var)
                cb.grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=2)
                if "CanManageUserPermissions" not in self.current_permissions:
                    cb.configure(state="disabled")
                self.permission_vars[perm] = var

        button_bar = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        button_bar.pack(pady=15, padx=20, fill="x")

        self.add_button = ctk.CTkButton(button_bar, text="➕ Add User", height=38, command=self._save_user)
        self.add_button.pack(side="left", expand=True, padx=(0, 10), fill="x")
        if "CanAddUser" not in self.current_permissions:
            self.add_button.configure(state="disabled")

        clear_btn = ctk.CTkButton(button_bar, text="🔄 Clear", height=38, fg_color="#9CA3AF", command=self._clear_fields)
        clear_btn.pack(side="left", expand=True, fill="x")
    
    def _save_user(self):
        uname = self.entry_username.get().strip()
        pwd = self.entry_password.get().strip()
        perms = [perm for perm, var in self.permission_vars.items() if var.get()]

        if not uname:
            messagebox.showerror("Missing Info", "Username is required.")
            return

        if self.selected_user_id:
            if "CanEditUser" not in self.current_permissions:
             messagebox.showwarning("Access Denied", "You do not have permission to update users.")
             return
            self.vm.edit_user(self.selected_user_id, uname)
            if pwd:
                self.vm.update_user_password(self.selected_user_id, pwd)
            if "CanManageUserPermissions" in self.current_permissions:
                self.vm.assign_permissions(uname, perms)
            messagebox.showinfo("Updated", f"User '{uname}' updated.")
        else:
            if "CanAddUser" not in self.current_permissions:
                messagebox.showwarning("Access Denied", "You do not have permission to add users.")
                return
            if not pwd:
                messagebox.showerror("Missing Info", "Password is required for new users.")
                return
            self.vm.add_user(uname, pwd)
            if "CanManageUserPermissions" in self.current_permissions:
                self.vm.assign_permissions(uname, perms)
            messagebox.showinfo("Success", f"User '{uname}' added.")

        self._clear_fields()
    
    def _clear_fields(self):
        self.entry_username.delete(0, "end")
        self.entry_password.delete(0, "end")
        for var in self.permission_vars.values():
            var.set(False)
        self.selected_user_id = None
        self.user_list.selection_remove(self.user_list.selection())
        self.add_button.configure(text="➕ Add User")
    
    def _open_edit_user_popup(self, username):
        user_id = self.vm.get_user_id_by_username(username)
        perms = self.vm.get_permissions_for_user(username)
        popup = EditUserPopupWindow(
            self,
            username=username,
            user_id=user_id,
            permissions=perms,
            vm=self.vm,
            refresh_callback=self._populate_user_list
        )
        popup.transient(self)     # Stay on top
        popup.grab_set()          # Freeze background
        popup.wait_window()       # Block until closed

class EditUserPopupWindow(ctk.CTkToplevel):
    def __init__(self, master, username, user_id, permissions, vm, refresh_callback):
        super().__init__(master)
        self.title(f"Editing: {username}")
        self.geometry("500x580")
        self.configure(fg_color="#F9FAFB")

        self.username = username
        self.user_id = user_id
        self.current_permissions = permissions or []
        self.vm = vm
        self.refresh_callback = refresh_callback
        self.permission_vars = {}

        ctk.CTkLabel(self, text=f"📝 Edit User: {username}", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=15)

        ctk.CTkLabel(self, text="👤 Username:", anchor="w", font=ctk.CTkFont(size=14)).pack(padx=20, anchor="w")
        self.entry_username = ctk.CTkEntry(self, width=300)
        self.entry_username.insert(0, username)
        self.entry_username.pack(pady=5)

        ctk.CTkLabel(self, text="🔒 New Password:", anchor="w", font=ctk.CTkFont(size=14)).pack(padx=20, anchor="w")
        self.entry_password = ctk.CTkEntry(self, width=300, placeholder_text="Leave blank to keep unchanged", show="*")
        self.entry_password.pack(pady=5)

        ctk.CTkLabel(self, text="🔐 Permissions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        scroll_frame = ctk.CTkScrollableFrame(self, height=220)
        scroll_frame.pack(padx=20, pady=(0, 10), fill="both", expand=False)

        permission_groups = {
            "Vehicle Management": ["CanViewVehicle","CanAddVehicle","CanEditVehicle","CanDeleteVehicle"],
            "User Management": ["CanAddUser", "CanEditUser", "CanDeleteUser", "CanManageUserPermissions"],
            "Customer Access": ["CanAddCustomer", "CanEditCustomer", "CanDeleteCustomer"],
            "Material Control": ["CanAddMaterial", "CanEditMaterial", "CanDeleteMaterial"],
            "Weighing": ["CanWeighEntry", "CanOverrideWeight", "CanEditWeighTransaction", "CanDeleteWeighTransaction", "CanPrintWeighSlip", "CanApplyWeighCharges"],
            "Reports": ["CanViewReports", "CanExportReports"]
        }

        for group, perms in permission_groups.items():
            group_label = ctk.CTkLabel(scroll_frame, text=group, font=ctk.CTkFont(weight="bold"))
            group_label.pack(anchor="w", pady=(10, 2))
            row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            row.pack(anchor="w", padx=10)
            for i, perm in enumerate(perms):
                var = tk.BooleanVar(value=perm in self.current_permissions)
                cb = ctk.CTkCheckBox(row, text=perm, variable=var)
                cb.grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=2)
                self.permission_vars[perm] = var

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(pady=15)

        save_btn = ctk.CTkButton(button_row, text="💾 Save Changes", command=self._save)
        save_btn.pack(side="left", padx=(0, 10))

        cancel_btn = ctk.CTkButton(button_row, text="❌ Cancel", fg_color="#9CA3AF", command=self.destroy)
        cancel_btn.pack(side="left")

    def _save(self):
        new_username = self.entry_username.get().strip()
        new_password = self.entry_password.get().strip()
        updated_perms = [perm for perm, var in self.permission_vars.items() if var.get()]

        if not new_username:
            messagebox.showerror("Input Error", "Username cannot be empty.")
            return

        if new_username != self.username:
            self.vm.edit_user(self.user_id, new_username)

        if new_password:
            self.vm.update_user_password(self.user_id, new_password)

        self.vm.assign_permissions(new_username, updated_perms)
        messagebox.showinfo("Success", f"User '{new_username}' updated successfully.")
        self.refresh_callback()
        self.destroy()


