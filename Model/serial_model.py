import serial
import serial.tools.list_ports
import threading
import queue
import logging
import re
import os
import json
import time

class SerialReaderModel:
    SETTINGS_FILE = "serial_reader_settings.json"

    def __init__(self):
        """Initializes the model with internal state variables."""
        self.serial_port = None
        self.serial_thread = None
        self.running = False
        self.connected = False
        self.data_queue = queue.Queue()
        self.partial_data = b""

        # Parsing parameters with default values
        self.start_of_text_ascii = 91
        self.end_of_text_ascii = 93
        self.start_prefixes = ["8", "S"] # Default prefixes
        self.expected_data_length = 7 
        self.enable_parsing = True

        # New trimming mode and start index
        self.trimming_mode = "prefix" # "none", "prefix", "index"
        self.start_index = 0 # Default start index

        # Data processing settings
        self.remove_zeros = False
        self.reverse_string = False
        self.filter_digits = False

        # Default serial port settings (used for initial UI population if no saved settings)
        self.port = "No Ports Found"
        self.baudrate = 115200
        self.bytesize = 8
        self.parity = "None" # Store as string for settings persistence
        self.stopbits = 1.0 # Store as float for settings persistence
        self.rtscts = False # Flow control

        # Default refresh rate for the view (not part of serial model, but needed for settings)
        self.refresh_rate = "Normal"

        # Callbacks for warnings (set by ViewModel)
        self._on_length_mismatch_callback = None 
        self._on_prefix_not_found_callback = None 
        self._on_invalid_start_index_callback = None # New callback for invalid start index

        self.load_settings() # Load settings on initialization

    def get_available_ports(self):
        """Returns a list of available serial ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            return ["No Ports Found"]
        return ports

    def connect_port(self, port, baudrate, databits, parity_str, stopbits_val, flowcontrol):
        """Opens the serial port with the specified parameters."""
        if self.serial_port and self.serial_port.is_open:
            logging.info("Port is already open.")
            return True

        if not port or port == "No Ports Found":
            logging.error("No serial port selected.")
            return False

        try:
            parity_dict = {
                "None": serial.PARITY_NONE,
                "Even": serial.PARITY_EVEN,
                "Odd": serial.PARITY_ODD,
                "Mark": serial.PARITY_MARK,
                "Space": serial.PARITY_SPACE
            }
            parity = parity_dict.get(parity_str, serial.PARITY_NONE)

            stopbits_dict = {
                1.0: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2.0: serial.STOPBITS_TWO
            }
            stopbits = stopbits_dict.get(stopbits_val, serial.STOPBITS_ONE)

            self.serial_port = serial.Serial(
                port=port, baudrate=baudrate, parity=parity, stopbits=stopbits,
                bytesize=databits, rtscts=flowcontrol, timeout=0.1
            )
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            self.connected = True
            
            # Store current successful connection parameters
            self.port = port
            self.baudrate = baudrate
            self.bytesize = databits
            self.parity = parity_str # Store string representation for settings
            self.stopbits = stopbits_val # Store float representation for settings
            self.rtscts = flowcontrol

            logging.info(f"Connected to {port}")
            return True
        except (serial.SerialException, ValueError) as e:
            logging.error(f"Failed to connect to port {port}: {e}")
            self.connected = False
            return False

    def disconnect_port(self):
        """Closes the serial port."""
        if self.running:
            self.stop_reading_data()
            
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                self.connected = False
                logging.info("Disconnected from serial port.")
            except Exception as e:
                logging.error(f"Error closing serial port: {e}")
            self.serial_port = None

    def start_reading_data(self, on_error_callback=None):
        """Starts the serial data reading thread."""
        if self.running or not self.connected or not self.serial_port.is_open:
            return

        self.running = True
        # Clear any old data in the queue
        with self.data_queue.mutex:
            self.data_queue.queue.clear()

        self.serial_thread = threading.Thread(
            target=self._read_serial_data_thread,
            args=(on_error_callback,),
            daemon=True
        )
        self.serial_thread.start()
        logging.info("Serial reading thread started.")

    def stop_reading_data(self):
        """Stops the serial data reading thread."""
        if not self.running:
            return

        self.running = False
        if self.serial_thread and self.serial_thread.is_alive():
            self.serial_thread.join(timeout=0.5)
            if self.serial_thread.is_alive():
                logging.warning("Serial read thread did not terminate gracefully.")
        logging.info("Serial reading thread stopped.")

    def _read_serial_data_thread(self, on_error_callback):
        """Continuously reads serial data and puts it into a queue."""
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.read(self.serial_port.in_waiting or 4096)
                if data:
                    self.data_queue.put(data)
                else:
                    time.sleep(0.01) # Avoid busy-waiting
            except serial.SerialException as e:
                logging.error(f"Serial port error during read: {e}")
                if on_error_callback:
                    on_error_callback(e)
                break
            except Exception as e:
                logging.error(f"Unexpected error during serial read: {e}")
                if on_error_callback:
                    on_error_callback(e)
                break

    def process_data(self, data):
        """Processes raw byte data into a formatted string based on parsing and processing settings."""
        self.partial_data += data
        processed_data_list = []

        if not self.enable_parsing: # If parsing is disabled, return raw data
            try:
                # Attempt to decode the entire buffer as raw data
                decoded_raw_data = self.partial_data.decode('utf-8', errors='ignore')
                self.partial_data = b"" # Clear the buffer as it's "raw"
                return [decoded_raw_data]
            except Exception as e:
                logging.error(f"Error decoding raw data: {e}")
                self.partial_data = b"" # Clear to prevent continuous errors
                return []

        while True:
            start_idx = self.partial_data.find(bytes([self.start_of_text_ascii]))
            end_idx = self.partial_data.find(bytes([self.end_of_text_ascii]), start_idx)

            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                raw_packet_content = self.partial_data[start_idx + 1:end_idx].decode('utf-8', errors='ignore')
                self.partial_data = self.partial_data[end_idx + 1:]

                processed_packet = raw_packet_content # Start with the full extracted content

                # Apply trimming based on selected mode
                if self.trimming_mode == "prefix" and self.start_prefixes:
                    found_prefix_index = -1
                    best_prefix_len = 0

                    for prefix in self.start_prefixes:
                        idx = raw_packet_content.find(prefix)
                        if idx != -1:
                            if found_prefix_index == -1 or idx < found_prefix_index or \
                               (idx == found_prefix_index and len(prefix) > best_prefix_len):
                                found_prefix_index = idx
                                best_prefix_len = len(prefix)
                                processed_packet = raw_packet_content[idx:] # Trim from the found prefix

                    if found_prefix_index == -1: # No prefix found within the packet
                        if self._on_prefix_not_found_callback:
                            self._on_prefix_not_found_callback(raw_packet_content, self.start_prefixes)
                        processed_packet = raw_packet_content # Still process the original content

                elif self.trimming_mode == "index":
                    if 0 <= self.start_index < len(raw_packet_content):
                        processed_packet = raw_packet_content[self.start_index:]
                    else:
                        if self._on_invalid_start_index_callback:
                            self._on_invalid_start_index_callback(raw_packet_content, self.start_index)
                        processed_packet = raw_packet_content # Still process the original content

                # If trimming_mode is "none", processed_packet remains raw_packet_content

                # --- CORRECTED ORDER OF PROCESSING FILTERS ---
                # 1. Filter digits first to ensure a clean numeric string
                if self.filter_digits:
                    processed_packet = self.filter_digits_only(processed_packet)
                
                # 2. Then remove leading zeros
                if self.remove_zeros:
                    processed_packet = self.remove_leading_zeros(processed_packet)
                
                # 3. Finally, reverse the string (if enabled)
                if self.reverse_string:
                    processed_packet = processed_packet[::-1]

                # Check for expected_data_length, but don't skip the packet
                if self.expected_data_length > 0 and len(processed_packet) != self.expected_data_length:
                    if self._on_length_mismatch_callback:
                        # Ensure the callback gets the already processed packet for consistency
                        self._on_length_mismatch_callback(processed_packet, self.expected_data_length)
                    # Do NOT continue/skip, the packet will still be added to processed_data_list

                processed_data_list.append(processed_packet)
            else:
                break # No full packets found

        return processed_data_list

    def remove_leading_zeros(self, text):
        """Removes leading zeros from a string, but handles decimal points."""
        if '.' in text:
            # If there's a decimal, find the part before it and remove leading zeros
            parts = text.split('.', 1)
            # Only remove leading zeros from the integer part if it's not just "0"
            if parts[0] == '0':
                # This handles cases like "0.123" to remain "0.123"
                return '0.' + parts[1]
            return re.sub(r'^0+', '', parts[0]) + '.' + parts[1]
        else:
            # If no decimal, remove leading zeros from the whole string
            # 'or '0'' ensures that if the string becomes empty (e.g., '000' -> ''), it becomes '0'
            return re.sub(r'^0+', '', text) or '0'

    def filter_digits_only(self, text):
        """Filters a string to contain only digits and a single decimal point."""
        filtered_text = re.sub(r'[^0-9.]', '', text)
        if filtered_text.count('.') > 1:
            # If there are multiple decimals, keep only the first one
            parts = filtered_text.split('.', 1)
            filtered_text = parts[0] + '.' + parts[1].replace('.', '')
        return filtered_text

    def update_parsing_parameters(self, enable_parsing, start_of_text, end_of_text, start_chars, expected_length, trimming_mode, start_index): 
        """Updates the parsing parameters from the View Model."""
        self.enable_parsing = enable_parsing
        try:
            self.start_of_text_ascii = int(start_of_text)
            self.end_of_text_ascii = int(end_of_text)
            self.start_prefixes = [char.strip() for char in start_chars.split(',') if char.strip()]
            self.expected_data_length = int(expected_length) if expected_length else 0 
            self.trimming_mode = trimming_mode
            self.start_index = int(start_index) if start_index else 0 # Ensure integer
            return True, "Parsing parameters updated successfully."
        except ValueError as ve:
            return False, f"Invalid parsing parameter: {ve}"

    def update_processing_settings(self, remove_zeros, reverse_string, filter_digits):
        """Updates data processing settings."""
        self.remove_zeros = remove_zeros
        self.reverse_string = reverse_string
        self.filter_digits = filter_digits

    def get_data_from_queue(self):
        """Retrieves and clears all data from the queue."""
        data_to_process = b''
        while not self.data_queue.empty():
            try:
                data_to_process += self.data_queue.get_nowait()
            except queue.Empty:
                pass
        return data_to_process

    def is_connected(self):
        return self.connected
    
    def is_reading(self):
        return self.running

    def get_current_settings(self):
        """
        Returns a dictionary of the model's current settings.
        This is used by the ViewModel to initialize the View's controls.
        """
        return {
            'port': self.port,
            'baudrate': self.baudrate,
            'databits': self.bytesize,
            'parity': self.parity, # Stored as string
            'stopbits': self.stopbits, # Stored as float
            'flowcontrol': self.rtscts,
            'enable_parsing': self.enable_parsing,
            'start_of_text_ascii': self.start_of_text_ascii,
            'end_of_text_ascii': self.end_of_text_ascii,
            'start_prefixes': ",".join(self.start_prefixes), # Return as comma-separated string
            'expected_data_length': self.expected_data_length, 
            'trimming_mode': self.trimming_mode,
            'start_index': self.start_index,
            'remove_zeros': self.remove_zeros,
            'reverse_string': self.reverse_string,
            'filter_digits': self.filter_digits,
            'refresh_rate': self.refresh_rate # Default value, as it's not stored in model's state directly
        }

    def load_settings(self):
        """Loads settings from a JSON file."""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self._apply_settings(settings)
                logging.info("Settings loaded from file.")
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error loading settings from {self.SETTINGS_FILE}: {e}")
                # Fallback to default settings if file is corrupt or invalid
                self._apply_settings(self.get_current_settings()) # Apply current defaults
        else:
            logging.info("Settings file not found. Using default settings.")
            self._apply_settings(self.get_current_settings()) # Apply current defaults

    def save_settings(self, settings):
        """Saves current settings to a JSON file."""
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            logging.info("Settings saved to file.")
        except Exception as e:
            logging.error(f"Error saving settings to {self.SETTINGS_FILE}: {e}")

    def _apply_settings(self, settings):
        """Applies loaded settings to the model's attributes."""
        self.port = settings.get('port', self.port)
        self.baudrate = settings.get('baudrate', self.baudrate)
        self.bytesize = settings.get('databits', self.bytesize)
        self.parity = settings.get('parity', self.parity)
        self.stopbits = settings.get('stopbits', self.stopbits)
        self.rtscts = settings.get('flowcontrol', self.rtscts)
        self.enable_parsing = settings.get('enable_parsing', self.enable_parsing)
        self.start_of_text_ascii = settings.get('start_of_text_ascii', self.start_of_text_ascii)
        self.end_of_text_ascii = settings.get('end_of_text_ascii', self.end_of_text_ascii)
        
        # start_prefixes comes as a comma-separated string from settings, convert back to list
        start_prefixes_str = settings.get('start_prefixes', ",".join(self.start_prefixes))
        self.start_prefixes = [char.strip() for char in start_prefixes_str.split(',') if char.strip()]

        self.expected_data_length = settings.get('expected_data_length', self.expected_data_length) 
        self.trimming_mode = settings.get('trimming_mode', self.trimming_mode)
        self.start_index = settings.get('start_index', self.start_index)

        self.remove_zeros = settings.get('remove_zeros', self.remove_zeros)
        self.reverse_string = settings.get('reverse_string', self.reverse_string)
        self.filter_digits = settings.get('filter_digits', self.filter_digits)
        self.refresh_rate = settings.get('refresh_rate', self.refresh_rate)

