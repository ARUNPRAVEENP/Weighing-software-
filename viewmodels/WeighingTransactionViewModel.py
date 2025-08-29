import datetime
import uuid
import tkinter as tk
import os # Added for path handling
import json # Added for config loading
import subprocess # Added for calling external print command
import sys # Added for PyInstaller path handling

from Model.WeighingTransactionModel import WeighingTransaction
from repositories.vehicle_repository import VehicleRepository
from repositories.material_repository import MaterialRepository
from repositories.customer_repository import CustomerRepository
from repositories.WeighingTransactionRepository import WeighingTransactionRepository
from viewmodels.pri import ReceiptPrinter # Added for printing functionality

class WeighingTransactionViewModel:
    """
    ViewModel for the Weighing Transaction, responsible for
    managing data flow between the View and the Repositories,
    and implementing the core weighing and linking logic.
    """
    def __init__(self, vehicle_repository: VehicleRepository,
                 material_repository: MaterialRepository,
                 customer_repository: CustomerRepository,
                 weighing_repository: WeighingTransactionRepository,
                 serial_view_model=None):

        self.vehicle_repository = vehicle_repository
        self.material_repository = material_repository
        self.customer_repository = customer_repository
        self.weighing_repository = weighing_repository
        self.serial_view_model = serial_view_model

        self.operator = tk.StringVar(value="")

        print("[DEBUG] WeighingTransactionViewModel: Initializing ViewModel.")

        # --- UI-bindable properties (StringVars for direct UI binding) ---
        self.transaction_guid_var = tk.StringVar(value="")
        self.vehicle_number = tk.StringVar()
        self.vehicle_type = tk.StringVar(value="Select Vehicle Type")
        self.customer = tk.StringVar(value="Select Customer")
        self.material_type = tk.StringVar(value="Select Material Type")
        self.first_weight = tk.StringVar(value="0.00")
        self.second_weight = tk.StringVar(value="0.00")
        self.net_weight = tk.StringVar(value="0.00")
        self.weight_type = tk.StringVar(value="Tare") # Default UI selection, but logic allows flexibility
        self.captured_weight = tk.StringVar(value="0.00")
        self.status = tk.StringVar(value="Pending")
        self.remarks = tk.StringVar(value="")
        self.charges = tk.StringVar(value="0.00")

        self.is_second_weighing = tk.BooleanVar(value=False)
        self.current_linked_transaction_id = None

        # Data for comboboxes (name -> ID mapping)
        self.vehicle_type_names = []
        self.material_type_names = []
        self.customer_names = []

        # Callbacks from View (set by the View)
        self.status_update_callback = None
        self.error_display_callback = None
        self.clear_form_callback = None
        self.load_form_callback = None
        self.view_update_callback = None
        self.show_confirmation_dialog_callback = None
        self.show_selection_dialog_callback = None

        # Transaction state
        self.current_transaction = None

        # Initialize data for comboboxes
        self._load_vehicle_types()
        self._load_material_types()
        self._load_customers()

        # Set up Traces for UI-bound variables
        self.vehicle_number.trace_add("write", self._on_vehicle_number_changed)
        self.first_weight.trace_add("write", self._calculate_net_weight)
        self.second_weight.trace_add("write", self._calculate_net_weight)
        self.weight_type.trace_add("write", self._on_weight_type_changed)
        self.vehicle_type.trace_add("write", self._on_vehicle_type_changed)
        self.material_type.trace_add("write", self._on_material_type_changed)
        self.customer.trace_add("write", self._on_customer_changed)

        # Initialize UI elements by clearing the form
        self.clear_form_fields()

    # --- Data Loading Methods ---
    def _load_vehicle_types(self):
        types = self.vehicle_repository.get_all()
        self._vehicle_types_data = {v.name: v.id for v in types}
        self.vehicle_type_names = list(self._vehicle_types_data.keys())
        # Use specific callback if available, otherwise general view_update_callback
        if hasattr(self, 'set_vehicle_type_options_callback') and self.set_vehicle_type_options_callback:
            self.set_vehicle_type_options_callback(self.vehicle_type_names)
        elif self.view_update_callback:
            self.view_update_callback({"vehicle_type_names": self.vehicle_type_names})

    def _load_material_types(self):
        types = self.material_repository.get_all()
        self._material_types_data = {m.name: m.id for m in types}
        self.material_type_names = list(self._material_types_data.keys())
        if hasattr(self, 'set_material_type_options_callback') and self.set_material_type_options_callback:
            self.set_material_type_options_callback(self.material_type_names)
        elif self.view_update_callback:
            self.view_update_callback({"material_type_names": self.material_type_names})

    def _load_customers(self):
        customers = self.customer_repository.get_all()
        self._customer_data = {c.name: c.id for c in customers}
        self.customer_names = list(self._customer_data.keys())
        if hasattr(self, 'set_customer_options_callback') and self.set_customer_options_callback:
            self.set_customer_options_callback(self.customer_names)
        elif self.view_update_callback:
            self.view_update_callback({"customer_names": self.customer_names})

    # --- Property Change Handlers ---
    def _on_vehicle_number_changed(self, *args):
        vehicle_num = self.vehicle_number.get().strip().upper()
        if vehicle_num:
            self._evaluate_vehicle_history(vehicle_num)
        else:
            self._reset_linking_state()
            self._setup_new_first_weighing()
            self.status.set("Enter Vehicle Number")
            if self.status_update_callback:
                self.status_update_callback("neutral")

    def _on_vehicle_type_changed(self, *args):
        selected_name = self.vehicle_type.get()
        vehicle_id = self._vehicle_types_data.get(selected_name)
        if self.current_transaction:
            self.current_transaction.vehicle_type_id = vehicle_id

    def _on_material_type_changed(self, *args):
        selected_name = self.material_type.get()
        material_id = self._material_types_data.get(selected_name)
        if self.current_transaction:
            self.current_transaction.material_type_id = material_id

    def _on_customer_changed(self, *args):
        selected_name = self.customer.get()
        customer_id = self._customer_data.get(selected_name)
        if self.current_transaction:
            self.current_transaction.customer_id = customer_id

    def _on_weight_type_changed(self, *args):
        # This trace handler mainly updates the status bar for user feedback
        if self.weight_type.get() == "Tare":
            self.status.set("Selected: Tare. Ready to capture.")
            if self.status_update_callback:
                self.status_update_callback("tare_ready")
        elif self.weight_type.get() == "Gross":
            self.status.set("Selected: Gross. Ready to capture.")
            if self.status_update_callback:
                self.status_update_callback("gross_ready")
        else: # For "Select Weight Type" or similar initial state
            self.status.set("Please select weight type (Tare/Gross) to capture.")
            if self.status_update_callback:
                self.status_update_callback("neutral")


    # --- Core Weighing Logic ---
    def capture_weight(self):
        if self.serial_view_model and hasattr(self.serial_view_model, "is_connected") and self.serial_view_model.is_connected.get():
            try:
                weight_val = float(self.serial_view_model.latest_processed_value.get())
                weight_str = f"{weight_val:.2f}"
                self.captured_weight.set(weight_str)

                now = datetime.datetime.now()
                current_weight_type_selection = self.weight_type.get()

                # Determine if this is the very first weight being captured for this transaction object
                # A transaction is "empty" if both first and second weights are 0.00
                is_transaction_empty = (float(self.first_weight.get()) == 0.00 and float(self.second_weight.get()) == 0.00)

                if is_transaction_empty:
                    # This is the first weight capture for this transaction
                    if current_weight_type_selection == "Tare":
                        self.first_weight.set(weight_str)
                        if self.current_transaction:
                            self.current_transaction.first_weight_timestamp = now
                        self.status.set("Tare Weight Captured. Ready for Gross Weighing.")
                        if self.status_update_callback:
                            self.status_update_callback("tare_captured")
                        self.weight_type.set("Gross") # Suggest next logical step
                        self.status.set("Ready for Second Weighing (Gross)")
                        if self.status_update_callback:
                            self.status_update_callback("gross_ready")

                    elif current_weight_type_selection == "Gross":
                        self.second_weight.set(weight_str)
                        if self.current_transaction:
                            self.current_transaction.second_weight_timestamp = now
                        self.status.set("Gross Weight Captured. Ready for Tare Weighing.")
                        if self.status_update_callback:
                            self.status_update_callback("gross_captured")
                        self.weight_type.set("Tare") # Suggest next logical step
                        self.status.set("Ready for Second Weighing (Tare)")
                        if self.status_update_callback:
                            self.status_update_callback("tare_ready")
                    else:
                        # Should not happen if UI enforces selection, but good for robustness
                        if self.error_display_callback:
                            self.error_display_callback("Validation Error", "Please select 'Tare' or 'Gross' before capturing the first weight.")
                        return
                else:
                    # This is the second weight capture for an existing (pending) transaction
                    # We ensure the *other* weight (the one currently zero) is being captured.
                    if current_weight_type_selection == "Tare":
                        if float(self.first_weight.get()) == 0.00: # Only set if tare is currently zero
                            self.first_weight.set(weight_str)
                            if self.current_transaction:
                                self.current_transaction.first_weight_timestamp = now
                            self.status.set("Tare Weight Captured. Transaction ready for completion.")
                            if self.status_update_callback:
                                self.status_update_callback("tare_captured")
                        else:
                            if self.error_display_callback:
                                self.error_display_callback("Logic Error", "Tare weight already captured for this transaction. Please ensure the correct weight type is selected.")
                            return
                    elif current_weight_type_selection == "Gross":
                        if float(self.second_weight.get()) == 0.00: # Only set if gross is currently zero
                            self.second_weight.set(weight_str)
                            if self.current_transaction:
                                self.current_transaction.second_weight_timestamp = now
                            self.status.set("Gross Weight Captured. Transaction ready for completion.")
                            if self.status_update_callback:
                                self.status_update_callback("gross_captured")
                        else:
                            if self.error_display_callback:
                                self.error_display_callback("Logic Error", "Gross weight already captured for this transaction. Please ensure the correct weight type is selected.")
                            return
                    else:
                        if self.error_display_callback:
                            self.error_display_callback("Validation Error", "Please select 'Tare' or 'Gross' for the second weighing.")
                        return

                self._calculate_net_weight()

            except ValueError:
                if self.error_display_callback:
                    self.error_display_callback("Error", "Invalid weight value from serial.")
                self.captured_weight.set("0.00")
        else:
            if self.error_display_callback:
                self.error_display_callback("Serial Port Error", "Serial port not connected or no weight received.")

    def _calculate_net_weight(self, *args):
        try:
            first = float(self.first_weight.get())
            second = float(self.second_weight.get())
            if first > 0 and second > 0:
                net = abs(second - first)
                self.net_weight.set(f"{net:.2f}")
                if self.current_transaction:
                    self.current_transaction.net_weight = net
            else:
                self.net_weight.set("0.00")
                if self.current_transaction:
                    self.current_transaction.net_weight = 0.00
        except ValueError:
            self.net_weight.set("0.00")
            if self.current_transaction:
                self.current_transaction.net_weight = 0.00

    # --- Transaction Management ---
    def save_transaction(self):
        self._populate_model_from_ui()

        # Basic validations (unchanged)
        if not self.current_transaction.vehicle_number:
            if self.error_display_callback:
                self.error_display_callback("Validation Error", "Vehicle Number cannot be empty.")
            return
        if not self.current_transaction.vehicle_type_id:
            if self.error_display_callback:
                self.error_display_callback("Validation Error", "Please select a Vehicle Type.")
            return
        if not self.current_transaction.material_type_id:
            if self.error_display_callback:
                self.error_display_callback("Validation Error", "Please select a Material Type.")
            return
        if not self.current_transaction.customer_id:
            if self.error_display_callback:
                self.error_display_callback("Validation Error", "Please select a Customer.")
            return

        # MODIFIED VALIDATION: Ensure at least one weight is captured before saving.
        if float(self.first_weight.get()) == 0.00 and float(self.second_weight.get()) == 0.00:
            if self.error_display_callback:
                self.error_display_callback("Validation Error", "At least one weight (Tare or Gross) must be captured to save the transaction.")
            return

        # Determine transaction status based on whether both weights are present
        if float(self.first_weight.get()) > 0 and float(self.second_weight.get()) > 0:
            self.current_transaction.status = 'Completed'
        else:
            # If only one weight is captured, it's a pending transaction
            self.current_transaction.status = 'Pending'

        self.current_transaction.operator_id = 1 # Replace with actual operator ID from login system

        material_type = self.material_repository.get_by_id(self.current_transaction.material_type_id)
        # Calculate charges only if transaction is completed and net weight exists
        if self.current_transaction.status == 'Completed' and material_type and material_type.charges is not None and self.current_transaction.net_weight is not None:
            calculated_charges = material_type.charges * self.current_transaction.net_weight
            self.current_transaction.charges = calculated_charges
            self.charges.set(f"{calculated_charges:.2f}")
        else:
            # Charges are 0.00 for pending transactions or if data is missing
            self.current_transaction.charges = 0.00
            self.charges.set("0.00")

        try:
            if self.current_transaction.id:
                self.weighing_repository.update(self.current_transaction)
                self.status.set(f"Transaction {self.current_transaction.transaction_guid[:8]}... Updated! Status: {self.current_transaction.status}")
                if self.status_update_callback:
                    self.status_update_callback("updated")
            else:
                self.weighing_repository.add(self.current_transaction)
                self.status.set(f"Transaction {self.current_transaction.transaction_guid[:8]}... Saved! Status: {self.current_transaction.status}")
                if self.status_update_callback:
                    self.status_update_callback("saved")

            self.clear_form_fields()
            self.load_transactions_for_display()
        except Exception as e:
            if self.error_display_callback:
                self.error_display_callback("Database Error", f"Failed to save transaction: {e}")
            self.status.set("Error saving transaction!")
            if self.status_update_callback:
                self.status_update_callback("error")

    def cancel_transaction(self):
        if self.current_transaction and self.current_transaction.id:
            try:
                self.current_transaction.status = 'Canceled'
                self.weighing_repository.update(self.current_transaction)
                self.status.set(f"Transaction {self.current_transaction.transaction_guid[:8]}... Canceled!")
                if self.status_update_callback:
                    self.status_update_callback("canceled")
                self.clear_form_fields()
                self.load_transactions_for_display()
            except Exception as e:
                if self.error_display_callback:
                    self.error_display_callback("Database Error", f"Failed to cancel transaction: {e}")
                self.status.set("Error canceling transaction!")
                if self.status_update_callback:
                    self.status_update_callback("error")
        else:
            self.clear_form_fields()
            self.status.set("Form cleared.")
            if self.status_update_callback:
                self.status_update_callback("neutral")

    def load_transactions_for_display(self):
        transactions = self.weighing_repository.get_all()
        transactions.sort(key=lambda x: x.created_at if isinstance(x.created_at, datetime.datetime) else datetime.datetime.min, reverse=True)
        display_data = []
        for t in transactions:
            vehicle_type_name = self._get_vehicle_type_name_by_id(t.vehicle_type_id)
            customer_name = self._get_customer_name_by_id(t.customer_id)
            material_type_name = self._get_material_type_name_by_id(t.material_type_id)
            # Display whichever weight was recorded first for clarity
            initial_weight_display = "0.00"
            initial_timestamp_display = "N/A"
            if t.first_weight is not None and t.first_weight > 0:
                initial_weight_display = f"{t.first_weight:.2f}"
                initial_timestamp_display = t.first_weight_timestamp.strftime('%Y-%m-%d %H:%M') if t.first_weight_timestamp else "N/A"
            elif t.second_weight is not None and t.second_weight > 0:
                initial_weight_display = f"{t.second_weight:.2f}"
                initial_timestamp_display = t.second_weight_timestamp.strftime('%Y-%m-%d %H:%M') if t.second_weight_timestamp else "N/A"


            display_data.append({
                "id": t.id,
                "transaction_guid": t.transaction_guid,
                "vehicle_number": t.vehicle_number,
                "vehicle_type": vehicle_type_name,
                "customer": customer_name,
                "material_type": material_type_name,
                "first_weight": f"{t.first_weight:.2f}" if t.first_weight is not None else "0.00",
                "first_weight_timestamp": t.first_weight_timestamp.strftime('%Y-%m-%d %H:%M') if t.first_weight_timestamp else "N/A",
                "second_weight": f"{t.second_weight:.2f}" if t.second_weight is not None else "0.00",
                "second_weight_timestamp": t.second_weight_timestamp.strftime('%Y-%m-%d %H:%M') if t.second_weight_timestamp else "N/A",
                "net_weight": f"{t.net_weight:.2f}" if t.net_weight is not None else "0.00",
                "status": t.status,
                "charges": f"{t.charges:.2f}" if t.charges is not None else "0.00",
                "remarks": t.remarks
            })
        if self.view_update_callback:
            self.view_update_callback(display_data)

    def load_transaction_into_form(self, transaction_guid):
        transaction = self.weighing_repository.get_by_guid(transaction_guid)
        if transaction:
            self.current_transaction = transaction
            self._populate_ui_from_model()
            self.is_second_weighing.set(True) # Assume linking for second weigh when loading
            
            # Determine which weight type needs to be captured next for the loaded transaction
            if (self.current_transaction.first_weight is None or self.current_transaction.first_weight == 0) and \
               (self.current_transaction.second_weight is not None and self.current_transaction.second_weight > 0):
                self.weight_type.set("Tare") # Gross was recorded first, so next is Tare
                self.status.set(f"Loaded Transaction {transaction_guid[:8]}... Ready for Tare Weighing.")
                if self.status_update_callback:
                    self.status_update_callback("tare_ready")
            elif (self.current_transaction.second_weight is None or self.current_transaction.second_weight == 0) and \
                 (self.current_transaction.first_weight is not None and self.current_transaction.first_weight > 0):
                self.weight_type.set("Gross") # Tare was recorded first, so next is Gross
                self.status.set(f"Loaded Transaction {transaction_guid[:8]}... Ready for Gross Weighing.")
                if self.status_update_callback:
                    self.status_update_callback("gross_ready")
            else:
                self.status.set(f"Loaded Transaction {transaction_guid[:8]}... (Completed or Incomplete)")
                if self.status_update_callback:
                    self.status_update_callback("neutral") # Or specific to completed/error
                self.weight_type.set("Tare") # Default, as no clear next step if already completed or fully empty
            
            if self.load_form_callback:
                self.load_form_callback()
        else:
            if self.error_display_callback:
                self.error_display_callback("Load Error", "Transaction not found.")
            self.status.set("Transaction not found.")
            if self.status_update_callback:
                self.status_update_callback("error")

    def _populate_model_from_ui(self):
        if not self.current_transaction:
            self.current_transaction = WeighingTransaction(
                transaction_guid=str(uuid.uuid4()),
                status='Pending'
            )
        self.current_transaction.vehicle_number = self.vehicle_number.get().strip().upper()
        self.current_transaction.first_weight = float(self.first_weight.get())
        self.current_transaction.second_weight = float(self.second_weight.get())
        self.current_transaction.net_weight = float(self.net_weight.get())
        self.current_transaction.remarks = self.remarks.get()
        # customer_id, material_type_id, vehicle_type_id are set by their respective trace handlers
        
        # Timestamps are now set directly in capture_weight when the specific weight is recorded.
        # No need to set them here during general populate.

    def _populate_ui_from_model(self):
        self.transaction_guid_var.set(self.current_transaction.transaction_guid if self.current_transaction.transaction_guid else "")
        self.vehicle_number.set(self.current_transaction.vehicle_number if self.current_transaction.vehicle_number else "")
        self.vehicle_type.set(self._get_vehicle_type_name_by_id(self.current_transaction.vehicle_type_id))
        self.customer.set(self._get_customer_name_by_id(self.current_transaction.customer_id))
        self.material_type.set(self._get_material_type_name_by_id(self.current_transaction.material_type_id))
        self.first_weight.set(f"{self.current_transaction.first_weight:.2f}" if self.current_transaction.first_weight is not None else "0.00")
        self.second_weight.set(f"{self.current_transaction.second_weight:.2f}" if self.current_transaction.second_weight is not None else "0.00")
        self.net_weight.set(f"{self.current_transaction.net_weight:.2f}" if self.current_transaction.net_weight is not None else "0.00")
        self.remarks.set(self.current_transaction.remarks if self.current_transaction.remarks else "")
        self.charges.set(f"{self.current_transaction.charges:.2f}" if self.current_transaction.charges is not None else "0.00")
        self.status.set(self.current_transaction.status if self.current_transaction.status else "Pending")

    def _reset_linking_state(self):
        self.is_second_weighing.set(False)
        self.current_linked_transaction_id = None
        self.first_weight.set("0.00")
        self.second_weight.set("0.00")
        self.net_weight.set("0.00")
        self.weight_type.set("Tare") # Reset UI selection default, but user can change

    def clear_form_fields(self):
        self.transaction_guid_var.set(str(uuid.uuid4()))
        self.vehicle_number.set("")
        self.vehicle_type.set("Select Vehicle Type")
        self.customer.set("Select Customer")
        self.material_type.set("Select Material Type")
        self.remarks.set("")
        self.charges.set("0.00")
        self.captured_weight.set("0.00")
        
        self._reset_linking_state()
        self._setup_new_first_weighing() # This will set the initial status
        
        if self.clear_form_callback:
            self.clear_form_callback()
        # Call _on_weight_type_changed to update status based on default "Tare" selection
        self._on_weight_type_changed() 

    def _setup_new_first_weighing(self):
        self._reset_linking_state()
        self.current_transaction = WeighingTransaction(
            transaction_guid=str(uuid.uuid4()),
            status='Pending'
        )
        self.is_second_weighing.set(False)
        self.weight_type.set("Tare") # Default selection for new entry, user can change in UI
        self._generate_new_entry_identifiers()
        self.status.set("New Entry: Ready for First Weighing (Select Tare or Gross)")
        if self.status_update_callback:
            self.status_update_callback("neutral")
        if self.load_form_callback:
            self.load_form_callback()

    def _setup_second_weighing(self, existing_transaction: WeighingTransaction):
        self.current_transaction = existing_transaction
        self.current_linked_transaction_id = existing_transaction.id
        self.is_second_weighing.set(True)
        self._populate_ui_from_model() # Load existing data into UI fields

        # Determine which weight needs to be captured next based on what's missing
        if (self.current_transaction.first_weight is None or self.current_transaction.first_weight == 0) and \
           (self.current_transaction.second_weight is not None and self.current_transaction.second_weight > 0):
            # Gross was recorded first, so the next expected weight is Tare
            self.weight_type.set("Tare")
            self.status.set(f"Linked to {existing_transaction.transaction_guid[:8]}... for Second Weighing (Tare)")
            if self.status_update_callback:
                self.status_update_callback("tare_ready")
        elif (self.current_transaction.second_weight is None or self.current_transaction.second_weight == 0) and \
             (self.current_transaction.first_weight is not None and self.current_transaction.first_weight > 0):
            # Tare was recorded first, so the next expected weight is Gross
            self.weight_type.set("Gross")
            self.status.set(f"Linked to {existing_transaction.transaction_guid[:8]}... for Second Weighing (Gross)")
            if self.status_update_callback:
                self.status_update_callback("gross_ready")
        else:
            # This case means both weights are already present (transaction completed), or neither is present (shouldn't be pending)
            self.status.set(f"Transaction {existing_transaction.transaction_guid[:8]} appears to be completed or empty.")
            if self.status_update_callback:
                self.status_update_callback("neutral")
            self.weight_type.set("Tare") # Default, as it's not a clear second weigh scenario

        if self.load_form_callback:
            self.load_form_callback()

    def _generate_new_entry_identifiers(self):
        new_guid = str(uuid.uuid4())
        if self.current_transaction:
            self.current_transaction.transaction_guid = new_guid
        self.transaction_guid_var.set(new_guid)
        # Only call if method exists
        if self.serial_view_model and hasattr(self.serial_view_model, "generate_new_serial_number"):
            self.serial_view_model.generate_new_serial_number()

    def _evaluate_vehicle_history(self, vehicle_num):
        pending_entries = self.weighing_repository.get_all_pending_by_vehicle_number(vehicle_num)
        if not pending_entries:
            self._handle_no_pending_entries()
        elif len(pending_entries) == 1:
            self._handle_single_pending_entry(pending_entries[0])
        else:
            self._handle_multiple_pending_entries(pending_entries)

    def _handle_no_pending_entries(self):
        self._setup_new_first_weighing()
        self.status.set(f"New entry initiated for {self.vehicle_number.get()}. Ready for first weigh.")
        if self.status_update_callback:
            self.status_update_callback("neutral") # Changed from tare_ready to neutral as it could be Gross

    def _handle_single_pending_entry(self, pending_entry):
        if self.show_confirmation_dialog_callback:
            date_str = pending_entry.first_weight_timestamp.strftime('%Y-%m-%d %H:%M') if pending_entry.first_weight_timestamp else "N/A"
            
            # Determine which type of weight is missing for the message
            missing_weight_type_for_message = "second weighing" # Default if unsure
            if (pending_entry.first_weight is None or pending_entry.first_weight == 0) and \
               (pending_entry.second_weight is not None and pending_entry.second_weight > 0):
                missing_weight_type_for_message = "Tare weighing" # Gross was recorded first
            elif (pending_entry.second_weight is None or pending_entry.second_weight == 0) and \
                 (pending_entry.first_weight is not None and pending_entry.first_weight > 0):
                missing_weight_type_for_message = "Gross weighing" # Tare was recorded first


            self.show_confirmation_dialog_callback(
                title="Link Weighing?",
                message=(f"A pending entry for vehicle {pending_entry.vehicle_number} "
                         f"(Initial Weight: {pending_entry.first_weight if pending_entry.first_weight else pending_entry.second_weight:.2f} kg, Date: {date_str}) "
                         f"was found. Do you want to link to this entry for the {missing_weight_type_for_message}?"),
                on_yes=lambda: self._setup_second_weighing(pending_entry),
                on_no=self._setup_new_first_weighing
            )

    def _handle_multiple_pending_entries(self, pending_entries):
        if self.show_selection_dialog_callback:
            options = []
            for entry in pending_entries:
                # Dynamically determine the displayed initial weight and timestamp
                first_recorded_weight = 0.00
                first_recorded_timestamp = None
                
                if entry.first_weight is not None and entry.first_weight > 0:
                    first_recorded_weight = entry.first_weight
                    first_recorded_timestamp = entry.first_weight_timestamp
                elif entry.second_weight is not None and entry.second_weight > 0:
                    first_recorded_weight = entry.second_weight
                    first_recorded_timestamp = entry.second_weight_timestamp

                date_str = first_recorded_timestamp.strftime('%Y-%m-%d %H:%M') if first_recorded_timestamp else "N/A"

                option_str = (f"ID: {entry.id}, GUID: {entry.transaction_guid[:8]}..., "
                              f"Initial Weight: {first_recorded_weight:.2f} kg, Date: {date_str}, Status: {entry.status}")
                options.append((option_str, entry))
            self.show_selection_dialog_callback(
                title="Select Entry to Link",
                message=f"Multiple pending entries found for vehicle {pending_entries[0].vehicle_number}. Please select one to link, or cancel to create a new entry.",
                options=options,
                on_select=lambda selected_entry_tuple: self._setup_second_weighing(selected_entry_tuple[1]),
                on_cancel=self._setup_new_first_weighing
            )

    # --- Helper methods for ID to Name conversion ---
    def _get_vehicle_type_name_by_id(self, type_id):
        for name, id_val in self._vehicle_types_data.items():
            if id_val == type_id:
                return name
        return "Unknown Vehicle Type"

    def _get_customer_name_by_id(self, customer_id):
        for name, id_val in self._customer_data.items():
            if id_val == customer_id:
                return name
        return "Unknown Customer"

    def _get_material_type_name_by_id(self, material_id):
        for name, id_val in self._material_types_data.items():
            if id_val == material_id:
                return name
        return "Unknown Material Type"

    def get_all_transactions(self):
        """
        Returns a list of all transaction dicts for the side panel.
        """
        transactions = self.weighing_repository.get_all()
        transactions.sort(key=lambda x: x.created_at if hasattr(x, "created_at") and x.created_at else datetime.datetime.min, reverse=True)
        display_data = []
        for t in transactions:
            vehicle_type_name = self._get_vehicle_type_name_by_id(t.vehicle_type_id)
            customer_name = self._get_customer_name_by_id(t.customer_id)
            material_type_name = self._get_material_type_name_by_id(t.material_type_id)
            display_data.append({
                "id": t.id,
                "transaction_guid": t.transaction_guid,
                "vehicle_number": t.vehicle_number,
                "vehicle_type": vehicle_type_name,
                "customer": customer_name,
                "material_type": material_type_name,
                "first_weight": f"{t.first_weight:.2f}" if t.first_weight is not None else "0.00",
                "first_weight_timestamp": t.first_weight_timestamp.strftime('%Y-%m-%d %H:%M') if t.first_weight_timestamp else "N/A",
                "second_weight": f"{t.second_weight:.2f}" if t.second_weight is not None else "0.00",
                "second_weight_timestamp": t.second_weight_timestamp.strftime('%Y-%m-%d %H:%M') if t.second_weight_timestamp else "N/A",
                "net_weight": f"{t.net_weight:.2f}" if t.net_weight is not None else "0.00",
                "status": t.status,
                "charges": f"{t.charges:.2f}" if t.charges is not None else "0.00",
                "remarks": t.remarks
            })
        return display_data

    def print_last_transaction(self):
        """
        Handles printing the most recent completed transaction.
        This logic was moved from the View to the ViewModel.
        """
        try:
            # Determine base directory depending on runtime environment
            if getattr(sys, 'frozen', False):
                base_dir = sys._MEIPASS  # PyInstaller bundle directory
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            # Load config file from bundled folder or source tree
            config_path = os.path.join(base_dir, "config.json")
            with open(config_path, "r") as f:
                config = json.load(f)

            # Resolve paths relative to base_dir
            config["database_path"] = os.path.join(base_dir, config.get("database_path", "weighbridge.db"))
            config["sumatra_path"] = os.path.join(base_dir, config.get("sumatra_path", "SumatraPDFcopy/SumatraPDF.exe"))

            # Setup printer and try printing the most recent transaction
            printer = ReceiptPrinter(config=config)
            
            # Get the last completed transaction for the current vehicle number, if available
            # Or, if no current vehicle, get the overall last completed transaction
            last_transaction = None
            if self.vehicle_number.get().strip():
                last_transaction = self.weighing_repository.get_latest_completed_transaction(self.vehicle_number.get().strip().upper())
            
            # If no specific vehicle transaction, get the absolute last transaction
            if not last_transaction:
                all_transactions = self.weighing_repository.get_all()
                completed_transactions = [t for t in all_transactions if t.status == 'Completed']
                if completed_transactions:
                    # Sort by last_updated_at or created_at to get the most recent one
                    completed_transactions.sort(key=lambda x: x.last_updated_at if x.last_updated_at else x.created_at, reverse=True)
                    last_transaction = completed_transactions[0]


            if last_transaction:
                pdf_path = printer.generate_receipt_pdf(last_transaction)
                print(f"📄 Receipt auto-printed from ViewModel: {pdf_path}")
                subprocess.call([
                    config["sumatra_path"],
                    "-print-to-default",
                    "-silent",
                    pdf_path
                ])
                self.status.set("Receipt printed successfully!")
                if self.status_update_callback:
                    self.status_update_callback("neutral") # Or a specific "printed" status
            else:
                self.status.set("No recent completed transaction found to print.")
                if self.status_update_callback:
                    self.status_update_callback("error") # Use error for "no transaction" scenario
        except FileNotFoundError as e:
            error_msg = f"Printing tool not found. Please check SumatraPDF path in config.json: {e}"
            print(f"❌ {error_msg}")
            if self.error_display_callback:
                self.error_display_callback("Printing Error", error_msg)
            self.status.set("Printing failed: Tool not found.")
            if self.status_update_callback:
                self.status_update_callback("error")
        except json.JSONDecodeError as e:
            error_msg = f"Error reading config.json: {e}"
            print(f"❌ {error_msg}")
            if self.error_display_callback:
                self.error_display_callback("Config Error", error_msg)
            self.status.set("Printing failed: Config error.")
            if self.status_update_callback:
                self.status_update_callback("error")
        except Exception as e:
            error_msg = f"An unexpected error occurred during printing: {e}"
            print(f"❌ {error_msg}")
            if self.error_display_callback:
                self.error_display_callback("Printing Error", error_msg)
            self.status.set("Printing failed.")
            if self.status_update_callback:
                self.status_update_callback("error")

