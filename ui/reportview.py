import customtkinter as ctk
import pandas as pd
from viewmodels.report_viewmodel import ReportViewModel
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, PageBreak
from reportlab.lib import colors
import os
import tkinter as tk

def export_to_pdf(file_path, df_data): 
    full_columns = [
        "Id", "TransactionGuid", "VehicleNumber", "VehicleTypeName",
        "MaterialName", "CustomerName", "FirstWeight", "FirstWeightTimestamp",
        "SecondWeight", "SecondWeightTimestamp", "NetWeight", "Charges",
        "Status", "OperatorName", "Remarks", "CreatedAt", "LastUpdatedAt"
    ]
    
    df = pd.DataFrame(df_data, columns=full_columns)

    for col in ["FirstWeightTimestamp", "SecondWeightTimestamp", "CreatedAt", "LastUpdatedAt"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M') if pd.notna(x) else None)
    
    column_chunks = [full_columns[i:i + 6] for i in range(0, len(full_columns), 6)]

    doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), rightMargin=10, leftMargin=10, topMargin=10, bottomMargin=10)
    story = []

    for chunk in column_chunks:
        data = [chunk] + df[chunk].values.tolist()
        col_widths = [150 if col in ["Remarks", "CreatedAt", "LastUpdatedAt", "TransactionGuid"]
                      else 110 if col in ["FirstWeightTimestamp", "SecondWeightTimestamp"]
                      else 90 for col in chunk]
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

    if story and isinstance(story[-1], PageBreak):
        story.pop()

    doc.build(story)

class ReportViewerFrame(ctk.CTkFrame):
    def __init__(self, parent, user_permissions):
        super().__init__(parent, fg_color="white")
        self.user_permissions = user_permissions
        self.vm = ReportViewModel()
        
        self.vm.load_available_dates() 
        print(f"DEBUG: ReportViewerFrame - Available dates for combo: {self.vm.available_dates}")
        
        self.vm.load_combined_filtered_transactions(
            column=None, 
            keyword=None, 
            date=self.vm.available_dates[0] if self.vm.available_dates else None
        )

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="🔄 Refresh Database", command=self.refresh_on_right_click)
        self.context_menu.add_command(label="📤 Export Transactions", command=self.export_data)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ Close", command=lambda: None)

        self.columns = [
            "Id", "TransactionGuid", "VehicleNumber", "VehicleTypeName",
            "MaterialName", "CustomerName",
            "FirstWeight", "FirstWeightTimestamp", "SecondWeight", "SecondWeightTimestamp",
            "NetWeight", "Charges", "Status", "OperatorName",
            "Remarks", "CreatedAt", "LastUpdatedAt"
        ]

        self._build_ui()
        self.refresh_table(self.vm.filtered_transactions)

    def _build_ui(self):
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(search_frame, text="Search:").pack(side="left", padx=5)
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=220)
        search_entry.pack(side="left", padx=5)

        self.filter_var = ctk.StringVar(value="VehicleNumber")
        filter_combo = ctk.CTkOptionMenu(search_frame, variable=self.filter_var,
                                         values=["VehicleNumber", "CustomerName", "MaterialName", "Status", "VehicleTypeName", "OperatorName"])
        filter_combo.pack(side="left", padx=5)

        search_entry.bind("<Return>", lambda e: self.perform_combined_filter())
        ctk.CTkButton(search_frame, text="Search", command=self.perform_combined_filter).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="Clear", command=self.clear_search).pack(side="left", padx=5)

        ctk.CTkLabel(search_frame, text="Filter by Date:").pack(side="left", padx=(20, 5))
        self.date_var = ctk.StringVar(value="All Dates")
        
        # --- MODIFIED LINE ---
        # Ensure values list is never empty, provide a default if vm.available_dates is empty
        date_combo = ctk.CTkOptionMenu(search_frame, variable=self.date_var,
                                       values=self.vm.available_dates if self.vm.available_dates else ["All Dates"]) 
        # --- END MODIFIED LINE ---
        
        date_combo.pack(side="left", padx=5)
        date_combo.set("All Dates")
        date_combo.bind("<ButtonRelease-1>", lambda e: self.perform_combined_filter())

        if "CanExportReports" in self.user_permissions:
            ctk.CTkButton(search_frame, text="Export", command=self.export_data).pack(side="left", padx=(20, 5))

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        import tkinter.ttk as ttk
        from tkinter import Scrollbar

        y_scroll = Scrollbar(table_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        x_scroll = Scrollbar(table_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings",
                                 yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.pack(expand=True, fill="both")
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        for col in self.columns:
            self.tree.heading(col, text=col)
            if col == "TransactionGuid":
                self.tree.column(col, width=150, anchor="center")
            elif col in ["FirstWeightTimestamp", "SecondWeightTimestamp", "CreatedAt", "LastUpdatedAt"]:
                self.tree.column(col, width=140, anchor="center")
            elif col == "Remarks":
                self.tree.column(col, width=200, anchor="w")
            else:
                self.tree.column(col, width=100, anchor="center")

        self.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def refresh_table(self, data):
        self.tree.delete(*self.tree.get_children())
        for row in data:
            values = [row.get(col, '') for col in self.columns]
            
            status = row.get("Status", "").lower()
            tag = "status_pending" if status == "pending" else "status_completed" if status == "completed" else "neutral"
            self.tree.insert('', 'end', values=values, tags=(tag,))
        self.tree.tag_configure("status_pending", background="#ffe5e5")
        self.tree.tag_configure("status_completed", background="#e6ffe6")
        self.tree.tag_configure("neutral", background="#f2f2f2")

    def perform_combined_filter(self):
        keyword = self.search_var.get()
        column = self.filter_var.get()
        date = self.date_var.get()
        
        if not keyword:
            column = None
            keyword = None

        try:
            self.vm.load_combined_filtered_transactions(column, keyword, date)
            self.refresh_table(self.vm.filtered_transactions)
        except ValueError as e:
            messagebox.showerror("Search Error", str(e))
            self.refresh_table([])

    def clear_search(self):
        self.search_var.set("")
        self.filter_var.set("VehicleNumber")
        self.date_var.set("All Dates")
        self.perform_combined_filter()

    def export_data(self):
        export_options = [("Excel file", "*.xlsx"), ("CSV file", "*.csv"), ("PDF file", "*.pdf")]
        file = filedialog.asksaveasfilename(title="Export Transactions",
                                            defaultextension=".xlsx",
                                            filetypes=export_options)
        if not file:
            return
        
        rows_to_export = self.vm.filtered_transactions or []
        if not rows_to_export:
            messagebox.showwarning("No Data", "There is no data to export.")
            return
        
        df = pd.DataFrame(rows_to_export, columns=self.columns)

        ext = os.path.splitext(file)[1].lower()
        try:
            if ext == ".csv":
                df.to_csv(file, index=False)
            elif ext == ".xlsx":
                df.to_excel(file, index=False)
            elif ext == ".pdf":
                messagebox.showwarning(
                    "Layout Warning",
                    "The PDF format may not display all columns cleanly due to wide layouts.\n\n"
                    "Large datasets or long fields like 'Remarks' and 'Timestamps' could be truncated or split across pages.\n"
                    "For best results, consider exporting to Excel or CSV instead.\n\n"
                    "PDF will attempt intelligent column splitting, but readability may vary."
                )
                export_to_pdf(file, df.to_dict('records'))
            else:
                raise ValueError("Unsupported format")
            messagebox.showinfo("Export Complete", f"Exported to:\n{file}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
    
    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def refresh_on_right_click(self):
        print("[Report] Right-click detected: refreshing transactions")
        self.perform_combined_filter()
