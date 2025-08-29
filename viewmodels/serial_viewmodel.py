import serial.tools.list_ports
import threading
import queue
import logging
import time
import os
import json
import tkinter as tk # Needed for BooleanVar, IntVar, and DoubleVar

# Assuming SerialReaderModel is in Model/serial_model.py
from Model.serial_model import SerialReaderModel

class SerialReaderViewModel:
    def __init__(self, model: SerialReaderModel):
        self.model = model
        
        # Tkinter variables for UI binding (these are the "trace_add" targets)
        self.is_connected = tk.BooleanVar(value=self.model.is_connected())
        self.is_reading = tk.BooleanVar(value=self.model.is_reading())
        self.available_ports = tk.StringVar(value=self._get_ports_string()) # Stores comma-separated ports

        # New: Tkinter DoubleVar to hold the latest processed numerical value
        self.latest_processed_value = tk.DoubleVar(value=0.0)

        # Callbacks to update the View
        self.view_update_callback = None # Function to update data display in View
        self.status_update_callback = None # Function to update status label/textarea in View
        self.error_callback = None # Function to show error messageboxes in View

        # New callbacks for specific warnings from the model
        self.prefix_not_found_callback = None
        self.invalid_start_index_callback = None

        # Set model's callbacks to ViewModel's methods
        self.model._on_length_mismatch_callback = self._handle_length_mismatch
        self.model._on_prefix_not_found_callback = self._handle_prefix_not_found
        self.model._on_invalid_start_index_callback = self._handle_invalid_start_index

        # Load initial settings from model (which loads from file)
        self.model.load_settings()
        self._update_ui_from_model_settings() # Update ViewModel's Tkinter vars based on loaded settings

    def _get_ports_string(self):
        """Helper to get available ports as a comma-separated string."""
        ports = self.model.get_available_ports()
        return ",".join(ports) if ports else ""

    def refresh_ports(self):
        """Refreshes the list of available serial ports."""
        ports = self.model.get_available_ports()
        self.available_ports.set(",".join(ports))
        if self.status_update_callback:
            self.status_update_callback(f"Ports refreshed: {', '.join(ports) if ports else 'No ports found'}")

    def connect_disconnect(self, port, baudrate, databits, parity_str, stopbits_val, flowcontrol):
        """Connects or disconnects the serial port."""
        if self.is_connected.get():
            # Delegate disconnection to the model
            self.model.disconnect_port()
            self.is_connected.set(False)
            self.is_reading.set(False) # Ensure reading state is also false
            if self.status_update_callback:
                self.status_update_callback("Disconnected.")
            return False
        else:
            try:
                # Convert string values from UI to appropriate types for the model
                baudrate_int = int(baudrate)
                databits_int = int(databits)
                stopbits_float = float(stopbits_val)

                connected = self.model.connect_port(port, baudrate_int, databits_int, parity_str, stopbits_float, flowcontrol)
                self.is_connected.set(connected) # Update Tkinter variable
                if connected:
                    if self.status_update_callback:
                        self.status_update_callback(f"Connected to {port} at {baudrate} baud.")
                else:
                    if self.error_callback:
                        self.error_callback(f"Failed to connect to {port}.")
                    if self.status_update_callback:
                        self.status_update_callback(f"Failed to connect to {port}.", is_error=True)
                return connected
            except ValueError as e:
                if self.error_callback:
                    self.error_callback(f"Invalid setting value: {e}")
                if self.status_update_callback:
                    self.status_update_callback(f"Invalid setting value: {e}", is_error=True)
                return False
            except Exception as e:
                if self.error_callback:
                    self.error_callback(f"An unexpected error occurred during connection: {e}")
                if self.status_update_callback:
                    self.status_update_callback(f"Connection error: {e}", is_error=True)
                return False

    def start_reading(self):
        """Starts reading data from the serial port."""
        if not self.is_connected.get():
            if self.status_update_callback:
                self.status_update_callback("Not connected to a serial port.", is_error=True)
            return

        def on_model_error(e):
            """Callback for errors originating in the model's reading thread."""
            if self.error_callback:
                self.error_callback(f"Serial read error: {e}")
            if self.status_update_callback:
                self.status_update_callback(f"Serial read error: {e}", is_error=True)
            self.stop_reading() # Automatically stop reading on error

        self.model.start_reading_data(on_error_callback=on_model_error) # Corrected call
        self.is_reading.set(True)
        if self.status_update_callback:
            self.status_update_callback("Started reading data.")

    def stop_reading(self):
        """Stops reading data from the serial port."""
        self.model.stop_reading_data()
        self.is_reading.set(False)
        if self.status_update_callback:
            self.status_update_callback("Stopped reading data.")

    def update_display_data(self):
        """
        Fetches raw data from the model's queue, processes it, and
        sends it to the view for display.
        This method is called periodically by the View.
        """
        raw_data = self.model.get_data_from_queue()
        if raw_data:
            # Process the raw data into a list of individual packets/lines
            processed_packets = self.model.process_data(raw_data)
            for packet in processed_packets:
                if self.view_update_callback:
                    self.view_update_callback(packet) # Pass each processed packet to the view
                
                # Attempt to convert the processed packet to a float and update latest_processed_value
                try:
                    numerical_value = float(packet)
                    self.latest_processed_value.set(numerical_value)
                except ValueError:
                    logging.warning(f"Processed packet '{packet}' could not be converted to a float. Not updating latest_processed_value.")
                    # Optionally, set to 0.0 or some indicator if conversion fails
                    # self.latest_processed_value.set(0.0) 

    def update_parsing_parameters(self, enable_parsing, start_of_text, end_of_text, start_chars, expected_length, trimming_mode, start_index):
        """Updates parsing parameters in the model."""
        success, message = self.model.update_parsing_parameters(
            enable_parsing, start_of_text, end_of_text, start_chars, expected_length, trimming_mode, start_index
        )
        if self.status_update_callback:
            self.status_update_callback(message, is_error=not success)
        if not success and self.error_callback:
            self.error_callback(message)

    def update_processing_settings(self, remove_zeros, reverse_string, filter_digits):
        """Updates data processing settings."""
        self.model.update_processing_settings(remove_zeros, reverse_string, filter_digits)
        if self.status_update_callback:
            self.status_update_callback("Data processing settings updated.")

    def save_settings(self, settings):
        """Saves current UI settings to the model for persistence."""
        self.model.save_settings(settings)
        if self.status_update_callback:
            self.status_update_callback("Settings saved.")

    def disconnect_port(self):
        """
        Public method to disconnect the port, called from the UI (e.g., dashboard closing).
        Delegates the call to the model.
        """
        self.model.disconnect_port()
        self.is_connected.set(False)
        self.is_reading.set(False)
        if self.status_update_callback:
            self.status_update_callback("Disconnected by dashboard close.")

    def _update_ui_from_model_settings(self):
        """
        Updates the ViewModel's Tkinter variables based on settings loaded from the model.
        This ensures the UI reflects the persisted settings on startup.
        """
        settings = self.model.get_current_settings()
        
        # Update available ports first, as port setting depends on it
        self.refresh_ports() # This will update self.available_ports Tkinter variable
        
        # Now set the selected port
        ports_list = self.model.get_available_ports()
        if settings['port'] in ports_list:
            self.available_ports.set(settings['port'])
        elif ports_list:
            self.available_ports.set(ports_list[0]) # Fallback to first available
        else:
            self.available_ports.set("No Ports Found")

        # For `is_connected` and `is_reading`, their state is managed by connect/disconnect/start/stop methods.
        # They reflect the *live* state, not just loaded settings.
        # Re-initialize the Tkinter variables to reflect the model's current state (e.g., if it was connected previously)
        self.is_connected.set(self.model.is_connected())
        self.is_reading.set(self.model.is_reading())

    def _handle_length_mismatch(self, packet_content, expected_length):
        """Handles length mismatch warning from the model."""
        if self.status_update_callback:
            self.status_update_callback(f"Warning: Packet '{packet_content}' length ({len(packet_content)}) != expected length ({expected_length}).", is_error=True)

    def _handle_prefix_not_found(self, packet_content, expected_prefixes):
        """Handles prefix not found warning from the model."""
        if self.status_update_callback:
            self.status_update_callback(f"Warning: Packet '{packet_content}' does not contain any of the expected prefixes: {', '.join(expected_prefixes)}. Processing original packet.", is_error=True)

    def _handle_invalid_start_index(self, packet_content, invalid_index):
        """Handles invalid start index warning from the model."""
        if self.status_update_callback:
            self.status_update_callback(f"Warning: Invalid start index {invalid_index} for packet '{packet_content}'. Index out of bounds. Processing original packet.", is_error=True)

