import subprocess
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
import json
import logging
from ttkwidgets.autocomplete import AutocompleteCombobox # Import the new widget
import os
import json
import subprocess
# Removed 'from viewmodels.pri import ReceiptPrinter' as printing logic moves to ViewModel
import sys


# Configure logging for the View
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WeighingTransactionView(ctk.CTkFrame):
    """
    View for the Weighing Transaction feature.
    Redesigned to look neat and clean, inspired by the provided image.
    Displays UI elements for transaction input, control, and data display.
    Binds to WeighingTransactionViewModel for data and logic.
    """
    def __init__(self, master, view_model):
        super().__init__(master, fg_color="transparent")
        self.view_model = view_model
        # Initialize entry_widgets dictionary for later use
        self.entry_widgets = {}
        print("[DEBUG] WeighingTransactionView initialized")

        # Set view callbacks in the ViewModel
        self.view_model.status_update_callback = self._update_status_label_color_from_vm
        self.view_model.error_display_callback = self.show_error_messagebox
        self.view_model.clear_form_callback = self.clear_form_fields
        self.view_model.load_form_callback = self.load_form_fields_from_viewmodel
        self.view_model.view_update_callback = self.update_transaction_display # Keep for potential future use or if VM updates other parts
        self.view_model.show_confirmation_dialog_callback = self._show_confirmation_dialog
        self.view_model.show_selection_dialog_callback = self._show_selection_dialog

        # New callbacks for ViewModel to push combobox options
        self.view_model.set_vehicle_type_options_callback = self._set_vehicle_type_combobox_options
        self.view_model.set_customer_options_callback = self._set_customer_combobox_options
        self.view_model.set_material_type_options_callback = self._set_material_type_combobox_options

        # --- Configure main grid layout for embedded panel ---
        self.grid_columnconfigure(0, weight=1) # Column for main input form
        self.grid_columnconfigure(1, weight=0) # Column for side panel (initially zero weight/hidden)
        self.grid_rowconfigure(0, weight=1) # Allow main_input_container row to expand

        # --- Right-click context menu for refresh ---
        self.popup_menu = tk.Menu(self, tearoff=0)
        self.popup_menu.add_command(label="Refresh", command=self.view_model.load_transactions_for_display)
        self.bind("<Button-3>", self._show_context_menu) # Bind right-click

        # --- Main Input Section Container ---
        # This frame will hold the left (details) and right (weight capture) sections
        main_input_container = ctk.CTkFrame(self, fg_color="transparent")
        # Placed in column 0 of the main view
        main_input_container.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        main_input_container.grid_columnconfigure((0, 1), weight=1, uniform="group1") # Uniform for equal width columns

        # --- Left Column: Transaction Details ---
        details_frame = ctk.CTkFrame(main_input_container, fg_color="transparent")
        details_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        details_frame.grid_columnconfigure(1, weight=1) # Make entry column expandable

        ctk.CTkLabel(details_frame, text="Weighing Transaction Entry",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # Sl. No. / Transaction GUID (Read-only)
        ctk.CTkLabel(details_frame, text="Sl. No.:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.transaction_guid_entry = ctk.CTkEntry(details_frame, textvariable=self.view_model.transaction_guid_var, state="readonly", width=200)
        self.transaction_guid_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['transaction_guid'] = self.transaction_guid_entry

        # Vehicle Number
        ctk.CTkLabel(details_frame, text="Vehicle Number:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.vehicle_number_entry = ctk.CTkEntry(details_frame, textvariable=self.view_model.vehicle_number, width=200)
        self.vehicle_number_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['vehicle_number'] = self.vehicle_number_entry

        # Vehicle Type Combobox
        ctk.CTkLabel(details_frame, text="Vehicle Type:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.vehicle_type_combobox = AutocompleteCombobox(details_frame, textvariable=self.view_model.vehicle_type, completevalues=[], width=200)
        self.vehicle_type_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['vehicle_type'] = self.vehicle_type_combobox


        # Customer Combobox
        ctk.CTkLabel(details_frame, text="Customer Name:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.customer_combobox = AutocompleteCombobox(details_frame, textvariable=self.view_model.customer, completevalues=[], width=200)
        self.customer_combobox.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['customer'] = self.customer_combobox


        # Material Type Combobox
        ctk.CTkLabel(details_frame, text="Material Type:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.material_type_combobox = AutocompleteCombobox(details_frame, textvariable=self.view_model.material_type, completevalues=[], width=200)
        self.material_type_combobox.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['material_type'] = self.material_type_combobox

        # Charges
        ctk.CTkLabel(details_frame, text="Charges:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.charges_entry = ctk.CTkEntry(details_frame, textvariable=self.view_model.charges, width=200)
        self.charges_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['charges'] = self.charges_entry

        # Remarks
        ctk.CTkLabel(details_frame, text="Remarks:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.remarks_entry = ctk.CTkEntry(details_frame, textvariable=self.view_model.remarks, width=200)
        self.remarks_entry.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        self.entry_widgets['remarks'] = self.remarks_entry

        # --- Right Column: Weight Capture ---
        weight_capture_frame = ctk.CTkFrame(main_input_container, fg_color="transparent")
        weight_capture_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        weight_capture_frame.grid_columnconfigure(0, weight=1) # Center content

        ctk.CTkLabel(weight_capture_frame, text="Weight Capture",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(0, 20), sticky="w")

        # Weight Type Radio Buttons (as per current code, image shows dropdown)
        # Keeping radio buttons for consistency with existing ViewModel binding
        weight_type_radio_frame = ctk.CTkFrame(weight_capture_frame, fg_color="transparent")
        weight_type_radio_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        weight_type_radio_frame.grid_columnconfigure((0,1,2), weight=1) # Distribute radio buttons

        ctk.CTkLabel(weight_type_radio_frame, text="Weight Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tare_radio = ctk.CTkRadioButton(weight_type_radio_frame, text="Tare", variable=self.view_model.weight_type, value="Tare")
        self.tare_radio.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.gross_radio = ctk.CTkRadioButton(weight_type_radio_frame, text="Gross", variable=self.view_model.weight_type, value="Gross")
        self.gross_radio.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Captured Weight (Large Display)
        self.captured_weight_label = ctk.CTkLabel(weight_capture_frame, textvariable=self.view_model.captured_weight,
                                                   font=ctk.CTkFont(size=48, weight="bold"), text_color="#FF8C00") # Orange color
        self.captured_weight_label.grid(row=2, column=0, padx=5, pady=20, sticky="ew")
        self.entry_widgets['captured_weight'] = self.captured_weight_label # Store label for clearing

        # Capture Weight Button
        self.capture_button = ctk.CTkButton(weight_capture_frame, text="Capture Weight",
                                             command=self.view_model.capture_weight,
                                             fg_color="#FFA500", hover_color="#FF8C00",
                                             font=ctk.CTkFont(size=16, weight="bold"),
                                             height=40, corner_radius=8)
        self.capture_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")

        # --- Hidden Weight Fields (Tare, Gross, Net) - kept for data visibility if needed ---
        # These are not prominently displayed in the image's input section,
        # but are crucial for the transaction data.
        # You can choose to hide them or place them elsewhere if they are not meant for direct input.
        # For now, placing them below the main input container, but they could be in 'details_frame'
        # or completely removed from this input view if only 'captured_weight' is user-facing.
        hidden_weights_frame = ctk.CTkFrame(self, fg_color="transparent")
        hidden_weights_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        hidden_weights_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1) # Distribute columns

        ctk.CTkLabel(hidden_weights_frame, text="Tare Weight:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.first_weight_entry = ctk.CTkEntry(hidden_weights_frame, textvariable=self.view_model.first_weight, state="readonly", width=100)
        self.first_weight_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.entry_widgets['first_weight'] = self.first_weight_entry

        ctk.CTkLabel(hidden_weights_frame, text="Gross Weight:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.second_weight_entry = ctk.CTkEntry(hidden_weights_frame, textvariable=self.view_model.second_weight, state="readonly", width=100)
        self.second_weight_entry.grid(row=0, column=3, padx=5, pady=2, sticky="ew")
        self.entry_widgets['second_weight'] = self.second_weight_entry

        ctk.CTkLabel(hidden_weights_frame, text="Net Weight:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.net_weight_entry = ctk.CTkEntry(hidden_weights_frame, textvariable=self.view_model.net_weight, state="readonly", width=100)
        self.net_weight_entry.grid(row=0, column=5, padx=5, pady=2, sticky="ew")
        self.entry_widgets['net_weight'] = self.net_weight_entry


        # --- Action Buttons ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=15, pady=10, sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2), weight=1) # Distribute buttons evenly

        self.save_button = ctk.CTkButton(button_frame, text="Save Entry", command=self.view_model.save_transaction,
                                         fg_color="green", hover_color="#4CAF50",
                                         font=ctk.CTkFont(size=16, weight="bold"),
                                         height=40, corner_radius=8)
        self.save_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.cancel_button = ctk.CTkButton(button_frame, text="Clear Form", command=self.view_model.cancel_transaction,
                                           fg_color="red", hover_color="#D32F2F",
                                           font=ctk.CTkFont(size=16, weight="bold"),
                                           height=40, corner_radius=8)
        self.cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # New "View Recent" button for side panel transition
        self.view_recent_button = ctk.CTkButton(button_frame, text="View Recent ▸",
                                                 command=self._on_view_recent_clicked,
                                                 fg_color="#6A5ACD", hover_color="#5A4ABF", # Purple color
                                                 font=ctk.CTkFont(size=16, weight="bold"),
                                                 height=40, corner_radius=8)
        self.view_recent_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)  # 🧩 Add 4th column

        self.print_recent_button = ctk.CTkButton(button_frame, text="🖨️ Print Recent",
                                          command=self.view_model.print_last_transaction, # <<< UPDATED COMMAND
                                          fg_color="#3F51B5", hover_color="#2C3E94",
                                          font=ctk.CTkFont(size=16, weight="bold"),
                                          height=40, corner_radius=8)
        self.print_recent_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")


        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.grid(row=3, column=0, padx=15, pady=5, sticky="ew") # Moved to row 3 to be below buttons

        # Initial population of comboboxes using ViewModel's properties
        # Assuming ViewModel's list properties are populated at this point
        self._set_vehicle_type_combobox_options(self.view_model.vehicle_type_names)
        self._set_customer_combobox_options(self.view_model.customer_names)
        self._set_material_type_combobox_options(self.view_model.material_type_names)

        # Initialize _side_panel attribute to None
        self._side_panel = None

    def _show_context_menu(self, event):
        """Displays the right-click context menu."""
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.popup_menu.grab_release()

    def update_transaction_display(self, data):
        """
        This method would typically update the main Treeview.
        Since the main Treeview is now in a side panel, this method's direct use for the main view is reduced.
        It might still be used by the ViewModel to update form fields after a transaction is loaded.
        If this method was solely for the main Treeview, it can be removed or adapted.
        For now, it remains as a placeholder, assuming ViewModel might call it for other updates.
        """
        logging.info("update_transaction_display called. Main Treeview is now in a side panel.")
        pass # No longer populating the main Treeview here

    def _on_tree_double_click(self, event):
        """
        Handles double-click on a treeview item to load the transaction into the form.
        This method was originally for the main Treeview.
        If double-click functionality is desired in the side panel, this logic needs to be
        bound to the Treeview within the side panel itself.
        """
        pass

    def _update_status_label_color_from_vm(self, status_type):
        """
        Updates the status label text and color based on the ViewModel's status.
        status_type can be "neutral", "error", "saved", "updated", "canceled", "tare_ready", "gross_ready", "tare_captured", "gross_captured"
        """
        status_text = self.view_model.status.get()
        color = "white" # Default neutral color

        if status_type == "error":
            color = "red"
        elif status_type == "saved":
            color = "green"
        elif status_type == "updated":
            color = "blue"
        elif status_type == "canceled":
            color = "orange"
        elif status_type == "tare_ready":
            color = "#4CAF50" # Greenish
        elif status_type == "gross_ready":
            color = "#2196F3" # Blueish
        elif status_type == "tare_captured":
            color = "#FFC107" # Amber
        elif status_type == "gross_captured":
            color = "#9C27B0" # Purple

        self.status_label.configure(text=status_text, text_color=color)

    def show_error_messagebox(self, title, message):
        """Displays an error message box."""
        messagebox.showerror(title, message, parent=self)

    def clear_form_fields(self):
        """Clears all input fields in the form."""
        # Clear CTkEntry and AutocompleteCombobox widgets
        for key, widget in self.entry_widgets.items():
            if isinstance(widget, ctk.CTkEntry):
                if widget.cget("state") == "readonly":
                    widget.configure(state="normal") # Temporarily make editable to clear
                    widget.delete(0, tk.END)
                    widget.configure(state="readonly")
                else:
                    widget.delete(0, tk.END)
            elif isinstance(widget, AutocompleteCombobox):
                widget.set("") # Clear combobox
            elif isinstance(widget, ctk.CTkLabel) and key == 'captured_weight':
                # For the captured_weight label, reset its textvariable
                self.view_model.captured_weight.set("0.00")
        
        # Reset radio buttons to default (Tare) - ViewModel will set the correct one on load_form_callback
        self.tare_radio.select()
        
        # Ensure comboboxes display default text (if ViewModel doesn't set them)
        # ViewModel's clear_form method should ideally handle resetting StringVars
        # self.view_model.vehicle_type.set("Select Vehicle Type") # ViewModel should do this
        # self.view_model.customer.set("Select Customer")
        # self.view_model.material_type.set("Select Material Type")


    def load_form_fields_from_viewmodel(self):
        """Loads data from ViewModel into form fields."""
        # This method is called by ViewModel after loading a transaction
        # The StringVars are already updated by ViewModel, so just refresh comboboxes
        # and ensure entry states are correct.
        
        # Set states for read-only fields
        self.transaction_guid_entry.configure(state="readonly")
        self.first_weight_entry.configure(state="readonly")
        self.second_weight_entry.configure(state="readonly")
        self.net_weight_entry.configure(state="readonly")
        self.charges_entry.configure(state="normal") # Charges can be edited
        self.captured_weight_label.configure(textvariable=self.view_model.captured_weight) # Ensure it's bound

        # Update combobox display if needed (though textvariable should handle this)
        self.vehicle_type_combobox.set(self.view_model.vehicle_type.get())
        self.customer_combobox.set(self.view_model.customer.get())
        self.material_type_combobox.set(self.view_model.material_type.get())

        # Set radio button based on weight_type
        if self.view_model.weight_type.get() == "Tare":
            self.tare_radio.select()
        else:
            self.gross_radio.select()

    def _set_vehicle_type_combobox_options(self, options_list):
        """Sets the completevalues for the vehicle type combobox."""
        if self.vehicle_type_combobox:
            self.vehicle_type_combobox.configure(completevalues=options_list)

    def _set_material_type_combobox_options(self, options_list):
        """Sets the completevalues for the material type combobox."""
        if self.material_type_combobox:
            self.material_type_combobox.configure(completevalues=options_list)

    def _set_customer_combobox_options(self, options_list):
        """Sets the completevalues for the customer combobox."""
        if self.customer_combobox:
            self.customer_combobox.configure(completevalues=options_list)

    def _show_confirmation_dialog(self, title, message, on_yes, on_no):
        """Shows a yes/no confirmation dialog."""
        response = messagebox.askyesno(title, message, parent=self) # Use parent for better dialog focus
        if response:
            on_yes()
        else:
            on_no()

    def _show_selection_dialog(self, title, message, options, on_select, on_cancel):
        """
        Shows a dialog to select from multiple options.
        options is a list of (display_string, actual_value) tuples.
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        def on_cancel_click(): # Nested function to access dialog and on_cancel
            on_cancel()
            dialog.destroy()

        # Handle window close (X) button as a cancel action
        dialog.protocol("WM_DELETE_WINDOW", on_cancel_click)

        ctk.CTkLabel(dialog, text=message, wraplength=380, justify="left").pack(pady=10, padx=10)

        listbox_frame = ctk.CTkFrame(dialog)
        listbox_frame.pack(pady=5, padx=10, fill="both", expand=True)

        listbox = tk.Listbox(
            listbox_frame,
            height=min(len(options), 10),
            selectmode=tk.SINGLE,
            background="#2b2b2b",
            foreground="white",
            selectbackground="#5E5E5E",
            selectforeground="white",
            highlightbackground="#3a3b3c",
            highlightcolor="#3a3b3c",
            bd=0,
            relief="flat"
        )
        listbox.pack(side="left", fill="both", expand=True)

        for i, (display_str, _) in enumerate(options):
            listbox.insert(tk.END, display_str)
        if options:
            listbox.selection_set(0)  # Default selection
        listbox.focus_set()           # Focus for keyboard navigation

        scrollbar = ctk.CTkScrollbar(listbox_frame, command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        def on_ok():
            try:
                selected_item_index = listbox.curselection()[0]
                on_select(*options[selected_item_index])
            except IndexError:
                on_cancel()
            finally: # Ensure dialog is destroyed in all cases
                dialog.destroy()

        dialog.bind("<Return>", lambda event: on_ok())
        dialog.bind("<Escape>", lambda event: on_cancel_click())

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=10)

        ok_button = ctk.CTkButton(button_frame, text="Select", command=on_ok,
                                  fg_color="green", hover_color="#4CAF50")
        # Added padx for more spacing between buttons
        ok_button.pack(side="left", padx=(5, 10)) # Add more right padding

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=on_cancel_click,
                                      fg_color="red", hover_color="#D32F2F")
        cancel_button.pack(side="left", padx=(10, 5)) # Add more left padding

        dialog.wait_window()

    def _on_view_recent_clicked(self):
        """
        Handles the click event for the 'View Recent' button.
        Shows the recent transactions side panel.
        """
        logging.info("View Recent button clicked. Showing recent transactions side panel.")
        self.show_recent_transactions_side_panel()

    def show_recent_transactions_side_panel(self):
        """Show the transaction Treeview in a right-side panel (embedded)."""
        # If panel exists and is visible, just lift it.
        if self._side_panel and self._side_panel.winfo_exists():
            self._side_panel.lift()
            return

        # Create the side panel frame
        self._side_panel = ctk.CTkFrame(self, fg_color="#2b2b2b") # Use a distinct background color
        # Grid it into column 1 of the main view, spanning all rows
        self._side_panel.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=(15, 15), pady=15)
        # Set column 1 to expand, making the side panel visible
        self.grid_columnconfigure(1, weight=1)

        # Style for Treeview (copied from previous popup implementation)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        bordercolor="#3a3b3c",
                        lightcolor="#3a3b3c",
                        darkcolor="#3a3b3c",
                        rowheight=25)
        style.map('Treeview', background=[('selected', '#5E5E5E')])
        style.configure("Treeview.Heading",
                        background="#3a3b3c",
                        foreground="white",
                        font=('TkDefaultFont', 10, 'bold'),
                        relief="flat")
        style.map("Treeview.Heading", background=[('active', '#4a4b4c')])

        # Frame for Treeview and Close button within the side panel
        panel_content_frame = ctk.CTkFrame(self._side_panel, fg_color="transparent")
        panel_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        panel_content_frame.grid_rowconfigure(0, weight=1) # Treeview row
        panel_content_frame.grid_columnconfigure(0, weight=1)

        columns = ("ID", "GUID", "Vehicle No.", "Vehicle Type", "Customer", "Material Type",
                   "Tare Weight", "Tare Timestamp", "Gross Weight", "Gross Timestamp",
                   "Net Weight", "Charges", "Status", "Remarks")

        tree = ttk.Treeview(panel_content_frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            if col == "Remarks":
                tree.column(col, width=150, anchor="center", stretch=True)
            else:
                tree.column(col, width=100, anchor="center")
        tree.column("GUID", width=120)
        tree.column("Vehicle No.", width=90)
        tree.column("Vehicle Type", width=100)
        tree.column("Customer", width=120)
        tree.column("Material Type", width=100)
        tree.column("Tare Weight", width=90)
        tree.column("Gross Weight", width=90)
        tree.column("Net Weight", width=90)
        tree.column("Tare Timestamp", width=120)
        tree.column("Gross Timestamp", width=120)
        tree.column("Charges", width=70)
        tree.column("Status", width=70)

        tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        scrollbar_y = ctk.CTkScrollbar(panel_content_frame, command=tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree.config(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ctk.CTkScrollbar(panel_content_frame, orientation="horizontal", command=tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        tree.config(xscrollcommand=scrollbar_x.set)

        # Double-click to load transaction and hide panel
        def _on_side_panel_tree_double_click(event):
            item_id = tree.focus()
            if item_id:
                self.view_model.load_transaction_into_form(item_id)
                self.hide_side_panel() # Call the new hide method
        tree.bind("<Double-1>", _on_side_panel_tree_double_click)

        # Populate data
        all_transactions = self.view_model.get_all_transactions()
        for row in all_transactions:
            tree.insert("", "end", iid=row["transaction_guid"],
                         values=(row["id"], row["transaction_guid"][:8] + "...", row["vehicle_number"],
                                 row["vehicle_type"], row["customer"], row["material_type"],
                                 row["first_weight"], row["first_weight_timestamp"],
                                 row["second_weight"], row["second_weight_timestamp"],
                                 row["net_weight"], row["charges"], row["status"], row["remarks"]))

        # Close button for the side panel
        close_button = ctk.CTkButton(panel_content_frame, text="Close", command=self.hide_side_panel,
                                     fg_color="red", hover_color="#D32F2F",
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     height=30, corner_radius=8)
        close_button.grid(row=2, column=0, pady=10, sticky="e")

    def hide_side_panel(self):
        """Hides the embedded side panel."""
        if self._side_panel and self._side_panel.winfo_exists():
            self._side_panel.destroy()
            self._side_panel = None
            # Collapse column 1 when the side panel is hidden
            self.grid_columnconfigure(1, weight=0)

    # Removed print_recent_transaction method from here as it's moved to ViewModel
    # def print_recent_transaction(self):
    #     # ... (logic moved to ViewModel) ...

