import customtkinter as ctk
import json
import sqlite3
from utils.resource_utils import  resource_path  # Your centralized path resolver
from resource_utils import resource_path
import os


class DiagnosticWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("System Readiness Check")
        self.geometry("400x360")
        self.configure(padx=20, pady=20)
        ctk.set_appearance_mode("light")

        self.status = ctk.CTkTextbox(self, width=360, height=280, wrap="word", corner_radius=8)
        self.status.pack(pady=10)

        self.status.insert("end", "🔍 Checking system components...\n\n")
        self.validate_all()
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=10)

    def append(self, text, success=True):
        symbol = "✅" if success else "❌"
        self.status.insert("end", f"{symbol} {text}\n")

    def validate_all(self):
        # Check DB
        db_path = resource_path("weighbridge.db")
        self.append(f"Database file found at: {db_path}", os.path.exists(db_path))
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                for tbl in ["Users", "VehicleTypes", "MaterialTypes", "Customers", "WeighingTransactions"]:
                    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl}'")
                    found = cur.fetchone()
                    self.append(f"Table `{tbl}` {'exists' if found else 'missing'}", bool(found))
                conn.close()
            except Exception as e:
                self.append(f"Error accessing DB: {e}", success=False)

        # Config file
        config_path = resource_path("config.json")
        self.append("Config file present", os.path.exists(config_path))
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    json.load(f)
                self.append("Config file loaded successfully")
            except Exception as e:
                self.append(f"Error parsing config: {e}", success=False)

        # PDF Viewer folder
        pdf_viewer = resource_path("SumatraPDFcopy")
        self.append("SumatraPDF folder present", os.path.exists(pdf_viewer))

        self.status.configure(state="disabled")