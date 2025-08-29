import customtkinter as ctk
import os
import sqlite3
import logging

# Import necessary view frames and view models
from ui.user_management_frame import UserManagementFrame
from ui.vehicle_type_frame import VehicleTypeFrame
from ui.material_type_frame import MaterialTypeFrame
from ui.customer_master_frame import CustomerMasterFrame
from ui.serial_reader_frame import SerialReaderView as SerialReaderFrame
from Model.serial_model import SerialReaderModel
from viewmodels.serial_viewmodel import SerialReaderViewModel
from ui.WeighingTransactionView import WeighingTransactionView
from viewmodels.WeighingTransactionViewModel import WeighingTransactionViewModel
from repositories.vehicle_repository import VehicleRepository
from repositories.material_repository import MaterialRepository
from repositories.customer_repository import CustomerRepository
from repositories.WeighingTransactionRepository import WeighingTransactionRepository
from repositories.user_repository import UserRepository
from Model.report_model import ReportRepository
from ui.reportview import ReportViewerFrame
from utils.resource_utils import resource_path

# Standard logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainDashboardFrame(ctk.CTkFrame):
    def __init__(self, master, username, user_permissions, db_path="weighbridge.db"):
        print("[DASHBOARD-LOG] ➡️ Initializing MainDashboardFrame...")
        super().__init__(master) 
        
        self.username = username
        self.user_permissions = user_permissions
        self.db_path = resource_path(db_path)
        
        # Configure the grid layout for this frame's children
        print("[DASHBOARD-LOG] Configuring main grid layout...")
        self.grid_rowconfigure(0, weight=0) # Row for header
        self.grid_rowconfigure(1, weight=0) # Row for menu
        self.grid_rowconfigure(2, weight=1) # Row for content container (should expand)
        self.grid_columnconfigure(0, weight=1)
        print("[DASHBOARD-LOG] Main grid layout configured.")

        # --- Initialize Repositories ---
        print("[DASHBOARD-LOG] Initializing repositories...")
        self.weighing_transaction_repo = WeighingTransactionRepository(db_path=self.db_path)
        self.vehicle_repo = VehicleRepository(db_path=self.db_path)
        self.material_repo = MaterialRepository(db_path=self.db_path)
        self.customer_repo = CustomerRepository(db_path=self.db_path)
        self.user_repo = UserRepository(db_path=self.db_path)
        self.report_repo = ReportRepository(db_path=self.db_path)
        print("[DASHBOARD-LOG] Repositories initialized.")

        # --- Initialize ViewModels ---
        print("[DASHBOARD-LOG] Initializing ViewModels...")
        self.serial_reader_model = SerialReaderModel()
        self.serial_reader_view_model = SerialReaderViewModel(model=self.serial_reader_model)
        self.weighing_transaction_view_model = WeighingTransactionViewModel(
            vehicle_repository=self.vehicle_repo,
            material_repository=self.material_repo,
            customer_repository=self.customer_repo,
            weighing_repository=self.weighing_transaction_repo,
            serial_view_model=self.serial_reader_view_model
        )
        self.weighing_transaction_view_model.operator.set(self.username)
        print("[DASHBOARD-LOG] ViewModels initialized.")

        self.frames = {}
        self.current_frame = None

        # --- Build UI Components ---
        self._build_header()
        self._build_menu()
        self._build_content_container()

        # Pre-initialize certain frames if necessary
        self._initialize_all_frames_for_callbacks()
        
        # Schedule the initial frame display
        print("[DASHBOARD-LOG] Scheduling 'home' frame to be shown.")
        self.after(100, lambda: self.show_frame("home"))
        
        print("[DASHBOARD-LOG] ✅ MainDashboardFrame initialization complete.")

    def cleanup_on_exit(self):
        """Performs necessary cleanup before the application closes."""
        print("[DASHBOARD-LOG] 🧹 Cleanup on exit called. Disconnecting serial port...")
        if self.serial_reader_view_model:
            self.serial_reader_view_model.disconnect_port()

    def _build_header(self):
        print("[DASHBOARD-LOG] Building header...")
        header = ctk.CTkFrame(self, fg_color="#1D4ED8", corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header,
            text="⚖ Weighbridge Admin Panel",
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        ).pack(padx=20, pady=15, anchor="w")
        print("[DASHBOARD-LOG] Header built.")

    def _build_menu(self):
        print("[DASHBOARD-LOG] Building menu...")
        menu = ctk.CTkFrame(self, fg_color="#E5E7EB")
        menu.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))

        self._add_menu_button(menu, "🏠 Home", lambda: self.show_frame("home"))
        self._add_menu_button(menu, "👤 User Management", lambda: self.show_frame("user_management"))
        self._add_menu_button(menu, "📦 Master", lambda: self.show_frame("master_section"))
        self._add_menu_button(menu, "🔌 Serial Reader", lambda: self.show_frame("serial_reader"))
        self._add_menu_button(menu, "⚙ Settings", lambda: self.show_frame("settings_section"))
        self._add_menu_button(menu, "📊 Reports", lambda: self.show_frame("report"))
        print("[DASHBOARD-LOG] Menu built.")

    def _build_content_container(self):
        print("[DASHBOARD-LOG] Building content container...")
        self.content_container = ctk.CTkFrame(self, corner_radius=12, fg_color="white")
        self.content_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=15)
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)
        print("[DASHBOARD-LOG] Content container built.")

    def _add_menu_button(self, parent, label, command):
        btn = ctk.CTkButton(
            parent, text=label, font=("Segoe UI", 16), height=40, width=160,
            corner_radius=8, fg_color="#3B82F6", hover_color="#2563EB", command=command
        )
        btn.pack(side="left", padx=(0, 10), pady=10)

    def _initialize_all_frames_for_callbacks(self):
        print("[DASHBOARD-LOG] Pre-initializing frames for callbacks...")
        # This is optional, but can help if frames need to exist before being shown
        # self._create_frame_instance("user_management")
        # self._create_frame_instance("serial_reader")
        print("[DASHBOARD-LOG] Frame pre-initialization complete.")

    def show_frame(self, frame_name):
        print(f"[DASHBOARD-LOG] 🖥️ Attempting to show frame: '{frame_name}'")
        
        if frame_name not in self.frames:
            print(f"[DASHBOARD-LOG] Frame '{frame_name}' not found in cache. Creating new instance...")
            frame = self._create_frame_instance(frame_name)
            if frame:
                self.frames[frame_name] = frame
            else:
                print(f"[DASHBOARD-LOG] ‼️ ERROR: Could not create frame: {frame_name}")
                return
            
        frame_to_show = self.frames[frame_name]
        
        if self.current_frame:
            print(f"[DASHBOARD-LOG] Hiding current frame: '{self.current_frame.winfo_class()}'")
            self.current_frame.grid_forget()

        print(f"[DASHBOARD-LOG] Placing frame '{frame_name}' on the grid.")
        frame_to_show.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame_to_show
        print(f"[DASHBOARD-LOG] ✅ Successfully showing frame: '{frame_name}'")

    def _create_frame_instance(self, frame_name):
        print(f"[DASHBOARD-LOG]   -> Creating instance for '{frame_name}'...")
        try:
            if frame_name == "home":
                return WeighingTransactionView(self.content_container, self.weighing_transaction_view_model)
            elif frame_name == "user_management":
                return UserManagementFrame(self.content_container, self.username, self.user_permissions)
            elif frame_name == "master_section":
                return self._create_master_frame()
            elif frame_name == "settings_section":
                return self._create_settings_frame()
            elif frame_name == "serial_reader":
                return SerialReaderFrame(self.content_container, self.serial_reader_view_model)
            elif frame_name == "vehicle_type":
                return VehicleTypeFrame(self.content_container, self.user_permissions, self.vehicle_repo)
            elif frame_name == "material_type":
                return MaterialTypeFrame(self.content_container, self.user_permissions, self.material_repo)
            elif frame_name == "customer_master":
                return CustomerMasterFrame(self.content_container, self.user_permissions, self.customer_repo)
            elif frame_name == "report":
                return ReportViewerFrame(self.content_container, self.user_permissions)
            else:
                # Fallback for unknown frame names
                fallback_frame = ctk.CTkFrame(self.content_container, fg_color="lightgray")
                ctk.CTkLabel(fallback_frame, text=f"Unknown Frame: {frame_name}", text_color="black").pack(pady=50)
                return fallback_frame
        except Exception as e:
            print(f"[DASHBOARD-LOG]   ‼️ CRITICAL ERROR while creating frame '{frame_name}': {e}")
            import traceback
            traceback.print_exc()
            return None # Return None if creation fails

    def _create_master_frame(self):
        master_frame = ctk.CTkFrame(self.content_container, fg_color="white")
        ctk.CTkLabel(master_frame, text="📦 Master Section", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        grid = ctk.CTkFrame(master_frame, fg_color="transparent")
        grid.pack(pady=10, padx=10, anchor="center")
        buttons = []
        if "CanViewVehicle" in self.user_permissions:
            buttons.append(("🚗 Vehicle Type", "vehicle_type"))
        buttons.append(("📦 Material Type", "material_type"))
        buttons.append(("👥 Customer Master", "customer_master"))
        for i, (text, frame_name) in enumerate(buttons):
            ctk.CTkButton(grid, text=text, width=220, height=100, font=("Segoe UI", 18, "bold"), corner_radius=12, 
                          fg_color="#3B82F6", hover_color="#2563EB", 
                          command=lambda fn=frame_name: self.show_frame(fn)).grid(row=0, column=i, padx=12, pady=12)
        return master_frame

    def _create_settings_frame(self):
        settings_frame = ctk.CTkFrame(self.content_container, fg_color="white")
        ctk.CTkLabel(settings_frame, text="⚙️ Settings", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
        grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
        grid.pack(pady=10, padx=10, anchor="center")
        if "CanViewReports" in self.user_permissions:
            ctk.CTkButton(grid, text="📊 Report Viewer", width=220, height=100, font=("Segoe UI", 18, "bold"), corner_radius=12, 
                          fg_color="#3B82F6", hover_color="#2563EB", 
                          command=lambda: self.show_frame("report")).grid(row=0, column=0, padx=12, pady=12)
        return settings_frame