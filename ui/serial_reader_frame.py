import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, messagebox
import logging
import datetime

class SerialReaderView(ctk.CTkFrame):
    def __init__(self, master, view_model):
        super().__init__(master, fg_color="transparent")
        self.view_model = view_model

        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

        self.scrollable_content_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.scrollable_content_frame.grid_columnconfigure(0, weight=2)
        self.scrollable_content_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_content_frame.grid_rowconfigure(0, weight=1)

        self.left_column_frame = ctk.CTkFrame(self.scrollable_content_frame, fg_color="transparent")
        self.left_column_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.left_column_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.left_column_frame.grid_columnconfigure(0, weight=1)

        self.right_column_frame = ctk.CTkFrame(self.scrollable_content_frame, fg_color="transparent")
        self.right_column_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_column_frame.grid_rowconfigure((0, 1), weight=1)
        self.right_column_frame.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self.setup_bindings()
        
        self.view_model.view_update_callback = self.update_display
        self.view_model.status_update_callback = self.update_status_label
        self.view_model.error_callback = self.show_error_messagebox
        # New callbacks for specific warnings
        self.view_model.prefix_not_found_callback = self.show_prefix_not_found_warning
        self.view_model.invalid_start_index_callback = self.show_invalid_start_index_warning

        self.load_settings_from_view_model()
        
    def create_widgets(self):
        # --- Serial Port Settings ---
        self.serial_settings_container = ctk.CTkFrame(self.left_column_frame, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#D1D5DB")
        self.serial_settings_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.serial_settings_container.grid_columnconfigure((0,1,2), weight=1)
        
        ctk.CTkLabel(self.serial_settings_container, text="Serial Port Settings", font=ctk.CTkFont(size=16, weight="bold"), text_color="#374151").grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(10, 10))
        
        self.port_label = ctk.CTkLabel(self.serial_settings_container, text="Serial Port:")
        self.port_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        self.port_combobox = ctk.CTkOptionMenu(self.serial_settings_container, width=180, values=["No Ports Found"])
        self.port_combobox.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.refresh_ports_button = ctk.CTkButton(self.serial_settings_container, text="Refresh Ports", command=self.refresh_ports_command, fg_color="#3B82F6", hover_color="#2563EB")
        self.refresh_ports_button.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        self.baudrate_label = ctk.CTkLabel(self.serial_settings_container, text="Baud Rate:")
        self.baudrate_label.grid(row=2, column=0, sticky="w", padx=15, pady=5)
        self.baudrates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
        self.baudrate_combobox = ctk.CTkOptionMenu(self.serial_settings_container, values=self.baudrates, width=180)
        self.baudrate_combobox.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.baudrate_combobox.set("115200")

        self.databits_label = ctk.CTkLabel(self.serial_settings_container, text="Data Bits:")
        self.databits_label.grid(row=3, column=0, sticky="w", padx=15, pady=5)
        self.data_bits = ["7", "8"]
        self.databits_combobox = ctk.CTkOptionMenu(self.serial_settings_container, values=self.data_bits, width=180)
        self.databits_combobox.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.databits_combobox.set("8")

        self.parity_label = ctk.CTkLabel(self.serial_settings_container, text="Parity:")
        self.parity_label.grid(row=4, column=0, sticky="w", padx=15, pady=5)
        self.parities = ["None", "Even", "Odd", "Mark", "Space"]
        self.parity_combobox = ctk.CTkOptionMenu(self.serial_settings_container, values=self.parities, width=180)
        self.parity_combobox.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        self.parity_combobox.set("None")

        self.stopbits_label = ctk.CTkLabel(self.serial_settings_container, text="Stop Bits:")
        self.stopbits_label.grid(row=5, column=0, sticky="w", padx=15, pady=5)
        self.stop_bits_options = ["1", "1.5", "2"]
        self.stopbits_combobox = ctk.CTkOptionMenu(self.serial_settings_container, values=self.stop_bits_options, width=180)
        self.stopbits_combobox.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        self.stopbits_combobox.set("1")

        self.flowcontrol_var = tk.BooleanVar()
        self.flowcontrol_check = ctk.CTkCheckBox(self.serial_settings_container, text="RTS/CTS Enabled", variable=self.flowcontrol_var, text_color="#374151")
        self.flowcontrol_check.grid(row=6, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        # --- Packet Parsing Settings ---
        self.parsing_ascii_container = ctk.CTkFrame(self.left_column_frame, fg_color="transparent")
        self.parsing_ascii_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.parsing_ascii_container.grid_columnconfigure((0,1), weight=1)
        self.parsing_ascii_container.grid_rowconfigure(0, weight=1)

        self.parsing_frame = ctk.CTkFrame(self.parsing_ascii_container, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#D1D5DB")
        self.parsing_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.parsing_frame.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(self.parsing_frame, text="Packet Parsing Settings", font=ctk.CTkFont(size=14, weight="bold"), text_color="#374151").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        self.enable_packet_parsing_var = tk.IntVar(value=1)
        self.enable_packet_parsing_check = ctk.CTkCheckBox(
            self.parsing_frame, text="Enable Packet Parsing", variable=self.enable_packet_parsing_var,
            command=self.toggle_parsing_inputs, text_color="#374151")
        self.enable_packet_parsing_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        self.startoftext_label = ctk.CTkLabel(self.parsing_frame, text="Start of Text (ASCII):")
        self.startoftext_label.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.startoftext_entry = ctk.CTkEntry(self.parsing_frame, width=100)
        self.startoftext_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.startoftext_entry.insert(0, "91")

        self.endoftext_label = ctk.CTkLabel(self.parsing_frame, text="End of Text (ASCII):")
        self.endoftext_label.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.endoftext_entry = ctk.CTkEntry(self.parsing_frame, width=100)
        self.endoftext_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        self.endoftext_entry.insert(0, "93")

        # --- Trimming Mode Selection ---
        self.trimming_mode_label = ctk.CTkLabel(self.parsing_frame, text="Trimming Mode:", text_color="#374151")
        self.trimming_mode_label.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        
        self.trimming_mode_var = tk.StringVar(value="prefix") # Default to prefix
        self.trimming_mode_none_radio = ctk.CTkRadioButton(self.parsing_frame, text="None", variable=self.trimming_mode_var, value="none", command=self.toggle_parsing_inputs, text_color="#374151")
        self.trimming_mode_none_radio.grid(row=5, column=0, sticky="w", padx=20, pady=2)
        self.trimming_mode_prefix_radio = ctk.CTkRadioButton(self.parsing_frame, text="Prefix", variable=self.trimming_mode_var, value="prefix", command=self.toggle_parsing_inputs, text_color="#374151")
        self.trimming_mode_prefix_radio.grid(row=6, column=0, sticky="w", padx=20, pady=2)
        self.trimming_mode_index_radio = ctk.CTkRadioButton(self.parsing_frame, text="Index", variable=self.trimming_mode_var, value="index", command=self.toggle_parsing_inputs, text_color="#374151")
        self.trimming_mode_index_radio.grid(row=7, column=0, sticky="w", padx=20, pady=2)

        # --- Prefix and Index Inputs ---
        self.startchar_label = ctk.CTkLabel(self.parsing_frame, text="Start Char(s) (e.g., 'A,B'):")
        self.startchar_label.grid(row=6, column=1, sticky="w", padx=5, pady=5) # Aligned with prefix radio
        self.startchar_entry = ctk.CTkEntry(self.parsing_frame, width=100)
        self.startchar_entry.grid(row=6, column=2, sticky="ew", padx=5, pady=5)
        self.startchar_entry.insert(0, "8,S")

        self.startindex_label = ctk.CTkLabel(self.parsing_frame, text="Start Index:")
        self.startindex_label.grid(row=7, column=1, sticky="w", padx=5, pady=5) # Aligned with index radio
        self.startindex_entry = ctk.CTkEntry(self.parsing_frame, width=100)
        self.startindex_entry.grid(row=7, column=2, sticky="ew", padx=5, pady=5)
        self.startindex_entry.insert(0, "0") # Default to 0

        self.datalength_label = ctk.CTkLabel(self.parsing_frame, text="Expected Data Length:")
        self.datalength_label.grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.data_lengths = [str(i) for i in range(0, 129)] # Changed range to include 0
        self.datalength_combobox = ctk.CTkOptionMenu(self.parsing_frame, values=self.data_lengths, width=100)
        self.datalength_combobox.grid(row=8, column=1, sticky="ew", padx=5, pady=5)
        self.datalength_combobox.set("7")

        self.apply_parsing_button = ctk.CTkButton(self.parsing_frame, text="Apply Parsing Settings", command=self.apply_parsing_settings_command, fg_color="#10B981", hover_color="#059669")
        self.apply_parsing_button.grid(row=9, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        self.apply_parsing_button.configure(state="disabled")

        # --- ASCII Converter ---
        self.ascii_frame = ctk.CTkFrame(self.parsing_ascii_container, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#D1D5DB")
        self.ascii_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.ascii_frame.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(self.ascii_frame, text="ASCII Converter", font=ctk.CTkFont(size=14, weight="bold"), text_color="#374151").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        self.char_input_label = ctk.CTkLabel(self.ascii_frame, text="Enter Character:")
        self.char_input_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.char_input_entry = ctk.CTkEntry(self.ascii_frame, width=50)
        self.char_input_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.convert_ascii_button = ctk.CTkButton(self.ascii_frame, text="Convert to ASCII", command=self.convert_char_to_ascii_command, fg_color="#6366F1", hover_color="#4F46E5")
        self.convert_ascii_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        self.ascii_output_label_text = ctk.CTkLabel(self.ascii_frame, text="ASCII Value:")
        self.ascii_output_label_text.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.ascii_output_label = ctk.CTkLabel(self.ascii_frame, text="", font=('Segoe UI', 10, 'bold'), text_color="blue")
        self.ascii_output_label.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # --- Data Processing Options ---
        self.processing_frame = ctk.CTkFrame(self.left_column_frame, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#D1D5DB")
        self.processing_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        self.processing_frame.grid_columnconfigure((0,1,2), weight=1)

        ctk.CTkLabel(self.processing_frame, text="Data Processing Options", font=ctk.CTkFont(size=14, weight="bold"), text_color="#374151").grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))

        self.remove_zeros_var = tk.IntVar()
        self.remove_zeros_check = ctk.CTkCheckBox(self.processing_frame, text="Remove Leading Zeros", variable=self.remove_zeros_var, command=self.update_processing_settings_command, text_color="#374151")
        self.remove_zeros_check.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        self.reverse_var = tk.IntVar()
        self.reverse_check = ctk.CTkCheckBox(self.processing_frame, text="Reverse String", variable=self.reverse_var, command=self.update_processing_settings_command, text_color="#374151")
        self.reverse_check.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        self.digits_var = tk.IntVar()
        self.digits_check = ctk.CTkCheckBox(self.processing_frame, text="Filter Digits Only", variable=self.digits_var, command=self.update_processing_settings_command, text_color="#374151")
        self.digits_check.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.refresh_label = ctk.CTkLabel(self.processing_frame, text="Refresh Rate:")
        self.refresh_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        self.refresh_rates = ["Normal", "Speed", "Slow"]
        self.refresh_combobox = ctk.CTkOptionMenu(self.processing_frame, values=self.refresh_rates, width=100)
        self.refresh_combobox.grid(row=2, column=2, sticky="ew", padx=5, pady=5)
        self.refresh_combobox.set("Normal")
        
        # --- Control Buttons ---
        self.button_frame = ctk.CTkFrame(self.left_column_frame, fg_color="transparent")
        self.button_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=10)
        self.button_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.connect_button = ctk.CTkButton(self.button_frame, text="Connect", command=self.connect_disconnect_command, fg_color="#3B82F6", hover_color="#2563EB")
        self.connect_button.grid(row=0, column=0, sticky="ew", padx=5)
        self.start_button = ctk.CTkButton(self.button_frame, text="Start Reading", command=self.start_reading_command, state="disabled", fg_color="#10B981", hover_color="#059669")
        self.start_button.grid(row=0, column=1, sticky="ew", padx=5)
        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop Reading", command=self.stop_reading_command, state="disabled", fg_color="#F59E0B", hover_color="#D97706")
        self.stop_button.grid(row=0, column=2, sticky="ew", padx=5)
        self.clear_button = ctk.CTkButton(self.button_frame, text="Clear Output", command=self.clear_text, fg_color="#6B7280", hover_color="#4B5563")
        self.clear_button.grid(row=0, column=3, sticky="ew", padx=5)
        
        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self.left_column_frame, text="Status: Disconnected", text_color="red", font=('Segoe UI', 12, 'bold'))
        self.status_label.grid(row=4, column=0, sticky="w", padx=10, pady=10)

        # --- Right Column Widgets ---
        # Serial Data Output
        self.serial_output_container = ctk.CTkFrame(self.right_column_frame, fg_color="#F9FAFB", corner_radius=10, border_width=1, border_color="#D1D5DB")
        self.serial_output_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.serial_output_container.grid_rowconfigure(1, weight=1)
        self.serial_output_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.serial_output_container, text="Serial Data Output", font=ctk.CTkFont(size=16, weight="bold"), text_color="#374151").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.text_area = scrolledtext.ScrolledText(self.serial_output_container, wrap=tk.WORD, font=("Courier New", 10), bg="#FFFFFF", fg="#333333", borderwidth=1, relief="sunken", height=15)
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.text_area.config(state=tk.DISABLED)

        # Status/Error Messages
        self.status_messages_container = ctk.CTkFrame(self.right_column_frame, fg_color="#FFFBE5", corner_radius=10, border_width=1, border_color="#FCD34D")
        self.status_messages_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.status_messages_container.grid_rowconfigure(1, weight=1)
        self.status_messages_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.status_messages_container, text="Status/Error Messages", font=ctk.CTkFont(size=16, weight="bold"), text_color="#374151").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.status_text_area = scrolledtext.ScrolledText(self.status_messages_container, wrap=tk.WORD, font=("Segoe UI", 9), bg="#FFFBE5", fg="#663300", borderwidth=1, relief="sunken", height=8)
        self.status_text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.status_text_area.config(state=tk.DISABLED)

    def setup_bindings(self):
        self.char_input_entry.bind("<Return>", lambda event: self.convert_char_to_ascii_command())
        
        self.view_model.is_connected.trace_add("write", lambda *args: self.update_connection_state())
        self.view_model.is_reading.trace_add("write", lambda *args: self.update_reading_state())
        self.trimming_mode_var.trace_add("write", lambda *args: self.toggle_parsing_inputs())


    def update_connection_state(self):
        connected = self.view_model.is_connected.get()
        start_button_state = "normal" if connected and not self.view_model.is_reading.get() else "disabled"

        state = 'disabled' if connected else 'normal'
        self.port_combobox.configure(state=state)
        self.baudrate_combobox.configure(state=state)
        self.databits_combobox.configure(state=state)
        self.parity_combobox.configure(state=state)
        self.stopbits_combobox.configure(state=state)
        self.flowcontrol_check.configure(state='disabled' if connected else 'normal')
        self.refresh_ports_button.configure(state='disabled' if connected else 'normal')
        self.text_area.config(state="normal" if connected else "disabled")
        
        self.connect_button.configure(text="Disconnect" if connected else "Connect", 
                                      fg_color="#EF4444" if connected else "#3B82F6",
                                      hover_color="#DC2626" if connected else "#2563EB")
        
        self.start_button.configure(state=start_button_state)

        self.toggle_parsing_inputs()
        
    def update_reading_state(self):
        reading = self.view_model.is_reading.get()
        self.start_button.configure(text="Stop Reading" if reading else "Start Reading",
                                    fg_color="#F59E0B" if reading else "#10B981",
                                    hover_color="#D97706" if reading else "#059669")
        
        self.start_button.configure(state="disabled" if reading else ("normal" if self.view_model.is_connected.get() else "disabled"))

        self.stop_button.configure(state="normal" if reading else "disabled")
        self.connect_button.configure(state="disabled" if reading else "normal")

    def toggle_parsing_inputs(self):
        enable_parsing = self.enable_packet_parsing_var.get() == 1
        trimming_mode = self.trimming_mode_var.get()
        is_connected = self.view_model.is_connected.get()

        # Enable/disable general parsing inputs
        parsing_state = 'normal' if enable_parsing else 'disabled'
        self.startoftext_entry.configure(state=parsing_state)
        self.endoftext_entry.configure(state=parsing_state)
        self.datalength_combobox.configure(state=parsing_state)
        self.startoftext_label.configure(state=parsing_state)
        self.endoftext_label.configure(state=parsing_state)
        self.datalength_label.configure(state=parsing_state)

        # Enable/disable prefix-related inputs
        prefix_state = 'normal' if enable_parsing and trimming_mode == 'prefix' else 'disabled'
        self.startchar_entry.configure(state=prefix_state)
        self.startchar_label.configure(state=prefix_state)
        
        # Enable/disable index-related inputs
        index_state = 'normal' if enable_parsing and trimming_mode == 'index' else 'disabled'
        self.startindex_entry.configure(state=index_state)
        self.startindex_label.configure(state=index_state)

        # Enable/disable trimming mode radio buttons
        radio_state = 'normal' if enable_parsing else 'disabled'
        self.trimming_mode_none_radio.configure(state=radio_state)
        self.trimming_mode_prefix_radio.configure(state=radio_state)
        self.trimming_mode_index_radio.configure(state=radio_state)
        self.trimming_mode_label.configure(state=radio_state)

        # The apply parsing button is active only if connected and parsing is enabled
        if is_connected and enable_parsing:
            self.apply_parsing_button.configure(state="normal")
        else:
            self.apply_parsing_button.configure(state="disabled")

    def refresh_ports_command(self):
        self.view_model.refresh_ports()
        ports = self.view_model.available_ports.get()
        if ports:
            self.port_combobox.configure(values=ports)
            self.port_combobox.set(ports[0])
            self.connect_button.configure(state="normal")
        else:
            self.port_combobox.configure(values=["No Ports Found"])
            self.port_combobox.set("No Ports Found")
            self.connect_button.configure(state="disabled")

    def connect_disconnect_command(self):
        if not self.view_model.is_connected.get() and self.port_combobox.get() == "No Ports Found":
            messagebox.showwarning("No Port Selected", "Please select a serial port.")
            return

        is_connected = self.view_model.connect_disconnect(
            self.port_combobox.get(),
            self.baudrate_combobox.get(),
            self.databits_combobox.get(),
            self.parity_combobox.get(),
            self.stopbits_combobox.get(),
            self.flowcontrol_var.get()
        )
        if is_connected:
            self.save_settings_command()

    def start_reading_command(self):
        self.view_model.start_reading()
        self.update_display_loop()
        
    def stop_reading_command(self):
        self.view_model.stop_reading()

    def update_display_loop(self):
        if self.view_model.is_reading.get():
            self.view_model.update_display_data()
            refresh_rate_map = {"Normal": 100, "Speed": 10, "Slow": 500}
            delay_ms = refresh_rate_map.get(self.refresh_combobox.get(), 100)
            self.after(delay_ms, self.update_display_loop)

    def update_display(self, data):
        self.text_area.config(state="normal")
        self.text_area.insert(tk.END, data + '\n')
        self.text_area.see(tk.END)
        self.text_area.config(state="disabled")

    def update_status_label(self, message, is_error=False):
        color = "red" if is_error else "green" if "Connected" in message else "blue" if "Reading" in message else "black"
        self.status_label.configure(text=f"Status: {message}", text_color=color)
        
        self.status_text_area.config(state="normal")
        self.status_text_area.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.status_text_area.see(tk.END)
        self.status_text_area.config(state="disabled")

    def show_prefix_not_found_warning(self, packet_content, expected_prefixes):
        """Displays a warning when no matching prefix is found."""
        message = f"Warning: Packet '{packet_content}' does not contain any of the expected prefixes: {', '.join(expected_prefixes)}. Processing original packet."
        self.update_status_label(message, is_error=True)

    def show_invalid_start_index_warning(self, packet_content, invalid_index):
        """Displays a warning when the start index is out of bounds."""
        message = f"Warning: Invalid start index {invalid_index} for packet '{packet_content}'. Index out of bounds. Processing original packet."
        self.update_status_label(message, is_error=True)

    def clear_text(self):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", ctk.END)
        self.text_area.config(state="disabled")
        self.status_text_area.config(state="normal")
        self.status_text_area.delete("1.0", ctk.END)
        self.status_text_area.config(state="disabled")

    def convert_char_to_ascii_command(self):
        char_input = self.char_input_entry.get()
        if len(char_input) == 1:
            ascii_value = ord(char_input)
            self.ascii_output_label.configure(text=str(ascii_value), text_color="blue")
        elif len(char_input) > 1:
            self.ascii_output_label.configure(text="Enter single char!", text_color="red")
        else:
            self.ascii_output_label.configure(text="No char entered", text_color="orange")
            
    def apply_parsing_settings_command(self):
        self.view_model.update_parsing_parameters(
            self.enable_packet_parsing_var.get() == 1,
            self.startoftext_entry.get(),
            self.endoftext_entry.get(),
            self.startchar_entry.get(),
            self.datalength_combobox.get(),
            self.trimming_mode_var.get(), # Pass trimming mode
            self.startindex_entry.get() # Pass start index
        )
        self.save_settings_command()

    def update_processing_settings_command(self):
        self.view_model.update_processing_settings(
            self.remove_zeros_var.get() == 1,
            self.reverse_var.get() == 1,
            self.digits_var.get() == 1
        )
        self.save_settings_command()

    def save_settings_command(self):
        settings = {
            'port': self.port_combobox.get(),
            'baudrate': int(self.baudrate_combobox.get()),
            'databits': int(self.databits_combobox.get()),
            'parity': self.parity_combobox.get(),
            'stopbits': float(self.stopbits_combobox.get()),
            'flowcontrol': self.flowcontrol_var.get(),
            'enable_parsing': self.enable_packet_parsing_var.get(),
            'start_of_text_ascii': int(self.startoftext_entry.get()),
            'end_of_text_ascii': int(self.endoftext_entry.get()),
            'start_prefixes': self.startchar_entry.get(),
            'expected_data_length': int(self.datalength_combobox.get()) if self.datalength_combobox.get() else 0,
            'trimming_mode': self.trimming_mode_var.get(), # Save trimming mode
            'start_index': int(self.startindex_entry.get()) if self.startindex_entry.get().isdigit() else 0, # Save start index
            'remove_zeros': self.remove_zeros_var.get(),
            'reverse_string': self.reverse_var.get(),
            'filter_digits': self.digits_var.get(),
            'refresh_rate': self.refresh_combobox.get()
        }
        self.view_model.save_settings(settings)

    def load_settings_from_view_model(self):
        current_model_settings = self.view_model.model.get_current_settings()
        
        available_ports = self.view_model.model.get_available_ports()
        if available_ports:
            self.port_combobox.configure(values=available_ports)
            if current_model_settings['port'] in available_ports:
                self.port_combobox.set(current_model_settings['port'])
            else:
                self.port_combobox.set(available_ports[0])
        else:
            self.port_combobox.configure(values=["No Ports Found"])
            self.port_combobox.set("No Ports Found")

        self.baudrate_combobox.set(str(current_model_settings['baudrate']))
        self.databits_combobox.set(str(current_model_settings['databits']))
        self.parity_combobox.set(current_model_settings['parity'])
        self.stopbits_combobox.set(str(current_model_settings['stopbits']))
        self.flowcontrol_var.set(current_model_settings['flowcontrol'])

        self.enable_packet_parsing_var.set(current_model_settings['enable_parsing'])
        self.startoftext_entry.delete(0, ctk.END)
        self.startoftext_entry.insert(0, str(current_model_settings['start_of_text_ascii']))
        self.endoftext_entry.delete(0, ctk.END)
        self.endoftext_entry.insert(0, str(current_model_settings['end_of_text_ascii']))
        self.startchar_entry.delete(0, ctk.END)
        self.startchar_entry.insert(0, current_model_settings['start_prefixes'])
        self.datalength_combobox.set(str(current_model_settings['expected_data_length']))
        
        # Load new trimming mode and start index
        self.trimming_mode_var.set(current_model_settings['trimming_mode'])
        self.startindex_entry.delete(0, ctk.END)
        self.startindex_entry.insert(0, str(current_model_settings['start_index']))

        self.remove_zeros_var.set(current_model_settings['remove_zeros'])
        self.reverse_var.set(current_model_settings['reverse_string'])
        self.digits_var.set(current_model_settings['filter_digits'])
        self.refresh_combobox.set(current_model_settings['refresh_rate'])
        
        self.toggle_parsing_inputs()

    def show_error_messagebox(self, message):
        messagebox.showerror("Error", message)

