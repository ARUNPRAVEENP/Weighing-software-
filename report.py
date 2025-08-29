import customtkinter as ctk
import pandas as pd
from viewmodels.report_viewmodel import ReportViewModel
from repositories.vehicle_repository import VehicleRepository
from tkinter import filedialog, messagebox
#from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
#from reportlab.lib.pagesizes import A4
#from reportlab.lib import colors
import os

from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib import colors
import math


ctk.set_appearance_mode("dark")      # or "light"
ctk.set_default_color_theme("blue")  # you can change this to "green", "dark-blue", etc.

vehicle_repo = VehicleRepository()
vehicle_cache = {}

def resolve_vehicle_type(vehicle_type_id):
    if vehicle_type_id not in vehicle_cache:
        vehicle = vehicle_repo.get_by_id(vehicle_type_id)
        vehicle_cache[vehicle_type_id] = vehicle.name if vehicle else "Unknown"
    return vehicle_cache[vehicle_type_id]

def export_to_pdf(file_path, df):
    # Define the full column layout
    full_columns = [
        "Id", "TransactionGuid", "VehicleNumber", "VehicleType",
        "MaterialName", "CustomerName", "FirstWeight", "FirstWeightTimestamp",
        "SecondWeight", "SecondWeightTimestamp", "NetWeight", "Charges",
        "Status", "OperatorName", "Remarks", "CreatedAt", "LastUpdatedAt"
    ]

    df = pd.DataFrame(df, columns=full_columns)

    # Split columns into chunks of 6 or 7 for better horizontal fitting
    column_chunks = [full_columns[i:i + 6] for i in range(0, len(full_columns), 6)]

    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    story = []

    for chunk in column_chunks:
        data = [chunk] + df[chunk].values.tolist()

        # Dynamic width allocation: wider space for Remarks and timestamps
        col_widths = []
        for col in chunk:
            if col in ["Remarks", "CreatedAt", "LastUpdatedAt", "TransactionGuid"]:
                col_widths.append(150)
            elif col in ["FirstWeightTimestamp", "SecondWeightTimestamp"]:
                col_widths.append(110)
            else:
                col_widths.append(90)

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#dcecf9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(table)
        story.append(PageBreak())

    # Remove last PageBreak to avoid blank page
    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)



def main():
    app = ctk.CTk()
    app.title("WeighBridge Studio")
    app.geometry("1300x700")

    vm = ReportViewModel()
    vm.load_available_dates()
    vm.load_all_transactions()

    # --- Top Controls ---
    search_frame = ctk.CTkFrame(app, fg_color="transparent")
    search_frame.pack(pady=10, padx=10, fill="x")

    ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
    search_var = ctk.StringVar()
    search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, width=220)
    search_entry.pack(side="left", padx=5)
    search_entry.focus()

    def perform_search():
        keyword = search_var.get()
        column = filter_var.get()
        try:
            vm.search_transactions(column, keyword)
            refresh_table(vm.filtered_transactions)
        except ValueError:
            refresh_table([])

    search_entry.bind("<Return>", lambda e: perform_search())

    filter_options = ["VehicleNumber", "CustomerName", "MaterialName", "Status", "VehicleType", "OperatorName"]
    filter_var = ctk.StringVar(value=filter_options[0])
    filter_combo = ctk.CTkOptionMenu(search_frame, variable=filter_var, values=filter_options)
    filter_combo.pack(side="left", padx=5)

    ctk.CTkButton(search_frame, text="Search", command=perform_search).pack(side="left", padx=5)
    ctk.CTkButton(search_frame, text="Clear", command=lambda: search_var.set("")).pack(side="left", padx=5)

    ctk.CTkLabel(search_frame, text="Filter by Date:").pack(side="left", padx=(20, 5))
    date_var = ctk.StringVar(value="All Dates")
    date_combo = ctk.CTkOptionMenu(search_frame, variable=date_var, values=vm.available_dates or ["All Dates"])
    date_combo.pack(side="left", padx=5)

    def filter_by_date():
        selected_date = date_var.get()
        if selected_date == "All Dates":
            vm.load_all_transactions()
            refresh_table(vm.filtered_transactions)
        else:
            vm.load_transactions_by_date(selected_date)
            refresh_table(vm.transactions_for_date)

    date_combo.set("All Dates")
    date_combo.bind("<ButtonRelease-1>", lambda e: filter_by_date())

    ctk.CTkButton(search_frame, text="Export", command=lambda: export_data()).pack(side="left", padx=(20, 5))

    # --- Scrollable Table (use tkinter Treeview inside frame) ---
    table_frame = ctk.CTkFrame(app)
    table_frame.pack(expand=True, fill="both", padx=10, pady=10)

    import tkinter.ttk as ttk  # fallback to standard Treeview inside CustomTkinter
    from tkinter import Scrollbar

    columns = [
        "Id", "TransactionGuid", "VehicleNumber", "VehicleType",
        "MaterialName", "CustomerName",
        "FirstWeight", "FirstWeightTimestamp", "SecondWeight", "SecondWeightTimestamp",
        "NetWeight", "Charges", "Status", "OperatorName", "Remarks", "CreatedAt", "LastUpdatedAt"
    ]

    y_scroll = Scrollbar(table_frame, orient="vertical")
    y_scroll.pack(side="right", fill="y")

    x_scroll = Scrollbar(table_frame, orient="horizontal")
    x_scroll.pack(side="bottom", fill="x")

    tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                        yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
    tree.pack(expand=True, fill="both")

    y_scroll.config(command=tree.yview)
    x_scroll.config(command=tree.xview)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=130, anchor="center")

    def refresh_table(data):
        tree.delete(*tree.get_children())
        for row in data:
            vt_name = resolve_vehicle_type(row.get("VehicleTypeId"))
            values = [row.get(col, '') if col != "VehicleType" else vt_name for col in columns]
            status = row.get("Status", "").lower()
            tag = "status_pending" if status == "pending" else "status_completed" if status == "completed" else "neutral"
            tree.insert('', 'end', values=values, tags=(tag,))
        tree.tag_configure("status_pending", background="#ffe5e5")
        tree.tag_configure("status_completed", background="#e6ffe6")
        tree.tag_configure("neutral", background="#f2f2f2")

    refresh_table(vm.filtered_transactions or [])

    def export_data():
        export_options = [("Excel file", "*.xlsx"), ("CSV file", "*.csv"), ("PDF file", "*.pdf")]
        file = filedialog.asksaveasfilename(title="Export Transactions", defaultextension=".xlsx", filetypes=export_options)
        if not file:
            return
        rows = vm.filtered_transactions or []
        if not rows:
            messagebox.showwarning("No Data", "There is no data to export.")
            return
        for row in rows:
            row["VehicleType"] = resolve_vehicle_type(row.get("VehicleTypeId"))
        #df = pd.DataFrame(rows)
        df = pd.DataFrame(rows, columns=[
        "Id", "TransactionGuid", "VehicleNumber", "VehicleType",
        "MaterialName", "CustomerName",
        "FirstWeight", "FirstWeightTimestamp", "SecondWeight", "SecondWeightTimestamp",
        "NetWeight", "Charges", "Status", "OperatorName", "Remarks", "CreatedAt", "LastUpdatedAt"
        ])
        ext = os.path.splitext(file)[1].lower()
        try:
            if ext == ".csv":
                df.to_csv(file, index=False)
            elif ext == ".xlsx":
                df.to_excel(file, index=False)
            elif ext == ".pdf":
                messagebox.showwarning(
                "Layout Warning",
                "The PDF format may not display all columns cleanly due to wide layouts.\n\n" +
                "Large datasets or long fields like 'Remarks' and 'Timestamps' could be truncated or split across pages.\n" +
                "For best results, consider exporting to Excel or CSV instead.\n\n" +
                "PDF will attempt intelligent column splitting, but readability may vary."
                )
                export_to_pdf(file, df)
            else:
                raise ValueError("Unsupported format")
            messagebox.showinfo("Export Complete", f"Exported to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    app.mainloop()

if __name__ == "__main__":
    main()