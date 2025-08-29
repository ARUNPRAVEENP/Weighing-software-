import sys
import os
import shutil # Needed for copying files

# Define constants for the database file and app name
# IMPORTANT: Customize _APP_NAME to your actual application's name.
_DB_FILENAME = "weighbridge.db"
_APP_NAME = "WeighderApp" # <<< CUSTOMIZE THIS TO YOUR APP'S NAME (e.g., "MyWeighbridge")

def resource_path(relative_path):
    """
    Resolves the absolute path for resources.
    
    For the main database file ('weighbridge.db'), it ensures the file is
    copied to a user-writable application data directory (e.g., AppData)
    on first run and returns that writable path. It will NOT overwrite
    an existing database in the writable location.
    
    For all other resources, it returns the path to the bundled resource,
    which might be a read-only location in a PyInstaller executable.

    Args:
        relative_path: The path to the resource relative to the script/bundle root.

    Returns:
        The absolute path to the resource, which will be writable for the database.
    """
    # --- Helper function to get writable AppData path (inlined for self-containment) ---
    def _get_writable_path_for_db_helper(db_filename_local: str, app_name_local: str) -> str:
        """Determines a user-writable directory for the database file."""
        if sys.platform.startswith('win'):
            # Windows: %APPDATA% (e.g., C:\Users\<User>\AppData\Roaming)
            base_dir_local = os.getenv('APPDATA')
            if not base_dir_local: # Fallback if APPDATA env var is not set
                base_dir_local = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        elif sys.platform.startswith('darwin'):
            # macOS: ~/Library/Application Support/
            base_dir_local = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
        else:
            # Linux/Unix: ~/.local/share/ for data files
            base_dir_local = os.path.join(os.path.expanduser("~"), ".local", "share")
            
        app_data_dir_local = os.path.join(base_dir_local, app_name_local)
        os.makedirs(app_data_dir_local, exist_ok=True) # Ensure the application's directory exists
        return os.path.join(app_data_dir_local, db_filename_local)
    # --- End of inlined helper logic ---

    # First, determine the base path for bundled resources (read-only)
    try:
        base_path = sys._MEIPASS  # Path set by PyInstaller for bundled resources
    except AttributeError:
        base_path = os.path.abspath(".") # Running from source (development environment)

    # --- Special handling for the database file ---
    if relative_path == _DB_FILENAME:
        writable_db_path = _get_writable_path_for_db_helper(_DB_FILENAME, _APP_NAME)
        
        # Check if the database already exists in the writable location
        if not os.path.exists(writable_db_path):
            print(f"INFO: Database '{_DB_FILENAME}' not found at writable path: {writable_db_path}.")
            print(f"Attempting to copy from bundled location: {os.path.join(base_path, relative_path)}")
            try:
                bundled_db_source_path = os.path.join(base_path, relative_path)
                # Ensure the source bundled path actually points to a file before attempting to copy
                if os.path.exists(bundled_db_source_path) and os.path.isfile(bundled_db_source_path):
                    shutil.copy2(bundled_db_source_path, writable_db_path)
                    print(f"INFO: Successfully copied '{_DB_FILENAME}' from bundled location to: {writable_db_path}")
                else:
                    # This warning occurs if the bundled DB is not found (e.g., in dev before it's created)
                    print(f"WARNING: Bundled database '{bundled_db_source_path}' not found or is not a file. A new database will be created at {writable_db_path} on first connection.")
            except Exception as e:
                # Catch any errors during the copy process (e.g., permission issues if writable_db_path is still problematic)
                print(f"ERROR: Failed to copy database '{_DB_FILENAME}' to writable location: {e}")
                print(f"Proceeding, but a new database might be created or errors might occur if {writable_db_path} is not writable.")
        else:
            print(f"INFO: Database '{_DB_FILENAME}' found at writable path: {writable_db_path}. Using existing file.")
        
        return writable_db_path # Return the writable path for the database
    # --- End of special handling for the database file ---

    else:
        # For all other resources (images, config files, etc.), return the path
        # to the bundled resource. This path might be read-only in a PyInstaller executable.
        return os.path.join(base_path, relative_path)

