import sys
import customtkinter as ctk
import tkinter as tk
import threading

from utils.resource_utils import resource_path
from viewmodels.login_viewmodel import LoginViewModel
from repositories.user_repository import UserRepository

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master):
        print("[LOGIN-LOG] ➡️  Initializing LoginWindow...")
        super().__init__(master)
        self.title("Weider Weighing & Automations - Login")
        
        self.geometry("900x600")
        self.resizable(False, False)
        
        # This flag is read by the main App to see if login was successful
        self.is_successful = False

        # --- Initialize Backend Components ---
        print("[LOGIN-LOG] Initializing backend components...")
        self.app_db_path = resource_path("weighbridge.db")
        self.repo = UserRepository(db_path=self.app_db_path)
        self.vm = LoginViewModel(self.repo)
        self._error_timer_id = None
        print("[LOGIN-LOG] Backend components initialized.")

        # --- Create UI Widgets ---
        print("[LOGIN-LOG] Creating UI widgets...")
        self.create_widgets()
        self.load_usernames()
        print("[LOGIN-LOG] UI widgets created.")
        
        # Center the window on the screen
        self.center_window()
        
        # Make this window modal (blocks interaction with the main window)
        self.grab_set()

        # Bind the Enter key to the login function
        self.bind('<Return>', lambda event: self.on_login_pressed())

        # Set the closing behavior for the window's 'X' button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        print("[LOGIN-LOG] ✅ LoginWindow initialization complete.")

    def on_closing(self):
        """Handle window closing event (e.g., clicking the 'X' button)."""
        print("[LOGIN-LOG] ❌ Login window closed by user.")
        self.cancel_pending_timers()
        self.is_successful = False
        self.destroy() # Closes this Toplevel window and lets the main app continue

    def center_window(self):
        """Centers the Toplevel window on the screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')

    def on_login_pressed(self):
        self.error_label.configure(text="")
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.display_error("Username and Password are required.")
            return

        self.vm.username = username
        self.vm.password = password

        if self.vm.login():
            print("[LOGIN-LOG] ✅ Login successful.")
            self.cancel_pending_timers()
            self.is_successful = True
            self.destroy() # Closes this Toplevel window on successful login
        else:
            print("[LOGIN-LOG] ‼️ Login failed.")
            self.display_error(self.vm.error_message or "Login failed. Please try again.")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus_set()

    def create_widgets(self):
        # This method contains your original UI layout code, which is correct.
        self.grid_columnconfigure(0, weight=1, minsize=450)
        self.grid_columnconfigure(1, weight=1, minsize=450)
        self.grid_rowconfigure(0, weight=1)

        # Left Section: Branding & Illustration
        self.left_frame = ctk.CTkFrame(self, fg_color="#E0E8F0", corner_radius=0) 
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure((0, 5), weight=1)

        self.logo_label = ctk.CTkLabel(self.left_frame, text="● Weider Weighing and automation", 
                                       font=ctk.CTkFont(size=30, weight="bold"), text_color="#3B82F6")
        self.logo_label.grid(row=1, column=0, pady=(50, 20), padx=40, sticky="w")
        
        self.illustration_placeholder = ctk.CTkLabel(self.left_frame, text="👨‍💻\n💻", 
                                                     font=ctk.CTkFont(size=100), text_color="#6B7280")
        self.illustration_placeholder.grid(row=2, column=0, pady=(20, 20))

        self.welcome_title_label = ctk.CTkLabel(self.left_frame, text="WELCOME", 
                                                font=ctk.CTkFont(size=28, weight="bold"), text_color="#374151")
        self.welcome_title_label.grid(row=3, column=0, pady=(20, 10), padx=40, sticky="w")
        
        self.welcome_desc_label = ctk.CTkLabel(self.left_frame, text="Here we go again", 
                                               font=ctk.CTkFont(size=14), text_color="#6B7280", justify="left")
        self.welcome_desc_label.grid(row=4, column=0, pady=(0, 50), padx=40, sticky="w")

        # Right Section: Login Form
        self.right_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0) 
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure((0, 10), weight=1)

        self.login_title_label = ctk.CTkLabel(self.right_frame, text="Login", 
                                              font=ctk.CTkFont(size=28, weight="bold"), text_color="#374151")
        self.login_title_label.grid(row=1, column=0, pady=(50, 10))

        self.no_account_text = ctk.CTkLabel(self.right_frame, text="Don't have an account? Create your account, it takes less\nthen a minute.", 
                                            font=ctk.CTkFont(size=13), text_color="#6B7280", justify="center")
        self.no_account_text.grid(row=2, column=0, pady=(0, 30))

        # Username
        self.username_label = ctk.CTkLabel(self.right_frame, text="User Name", anchor="w", font=ctk.CTkFont(size=12), text_color="#6B7280")
        self.username_label.grid(row=3, column=0, padx=50, pady=(5, 0), sticky="ew")
        self.username_entry = ctk.CTkEntry(self.right_frame, placeholder_text="", width=350, height=40, corner_radius=5, font=ctk.CTkFont(size=15), fg_color="white", text_color="black", border_color="#D1D5DB", border_width=1)
        self.username_entry.grid(row=4, column=0, padx=50, pady=(0, 20), sticky="ew")
        self.username_entry.bind("<FocusIn>", lambda e: self.username_entry.configure(border_color="#3B82F6"))
        self.username_entry.bind("<FocusOut>", lambda e: self.username_entry.configure(border_color="#D1D5DB"))

        # Password
        self.password_label = ctk.CTkLabel(self.right_frame, text="Password", anchor="w", font=ctk.CTkFont(size=12), text_color="#6B7280")
        self.password_label.grid(row=5, column=0, padx=50, pady=(5, 0), sticky="ew")
        self.password_entry = ctk.CTkEntry(self.right_frame, placeholder_text="", show="*", width=350, height=40, corner_radius=5, font=ctk.CTkFont(size=15), fg_color="white", text_color="black", border_color="#D1D5DB", border_width=1)
        self.password_entry.grid(row=6, column=0, padx=50, pady=(0, 10), sticky="ew")
        self.password_entry.bind("<FocusIn>", lambda e: self.password_entry.configure(border_color="#3B82F6"))
        self.password_entry.bind("<FocusOut>", lambda e: self.password_entry.configure(border_color="#D1D5DB"))

        # Controls
        self.remember_me_checkbox = ctk.CTkCheckBox(self.right_frame, text="Remember me", font=ctk.CTkFont(size=13), text_color="#6B7280", fg_color="#3B82F6", hover_color="#2563EB")
        self.remember_me_checkbox.grid(row=7, column=0, padx=50, pady=(0, 20), sticky="w")
        
        self.login_button = ctk.CTkButton(self.right_frame, text="LOGIN", command=self.on_login_pressed, width=350, height=45, corner_radius=5, font=ctk.CTkFont(size=16, weight="bold"), fg_color="#3B82F6", hover_color="#2563EB")
        self.login_button.grid(row=8, column=0, padx=50, pady=(0, 15), sticky="ew")

        self.forgot_password_label = ctk.CTkLabel(self.right_frame, text="Forgot Password?", font=ctk.CTkFont(size=13), text_color="#6B7280", cursor="hand2")
        self.forgot_password_label.grid(row=9, column=0, pady=(0, 40))
        self.forgot_password_label.bind("<Button-1>", lambda e: print("Forgot Password clicked!"))
        
        self.error_label = ctk.CTkLabel(self.right_frame, text="", text_color="red", font=ctk.CTkFont(size=13))
        self.error_label.grid(row=10, column=0, pady=(0, 10))

    def load_usernames(self):
        pass

    def display_error(self, message):
        """Displays an error message for 3 seconds."""
        self.error_label.configure(text=message)
        if self._error_timer_id:
            self.after_cancel(self._error_timer_id)
        self._error_timer_id = self.after(3000, lambda: self.error_label.configure(text=""))

    def cancel_pending_timers(self):
        """Cancels any pending Tkinter .after() calls."""
        if self._error_timer_id:
            try:
                self.after_cancel(self._error_timer_id)
            except Exception as e:
                print(f"Error cancelling timer (ID: {self._error_timer_id}): {e}")
            self._error_timer_id = None