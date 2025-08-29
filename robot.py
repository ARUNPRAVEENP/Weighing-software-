import customtkinter as ctk
import tkinter as tk
import time
from PIL import Image # Required for CTkImage to handle images

# Set the appearance mode to Light for a brighter, shinier base
ctk.set_appearance_mode("Light")
# Set the default color theme to "blue" for accents, but we'll use custom colors for the glassy effect
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window for a clean, spacious design
        self.title("Secure Login")
        self.geometry("500x550") # Increased height to accommodate avatar
        self.resizable(False, False) # Keep non-resizable for fixed layout consistency

        # Set the main window's background to a very light, almost white color
        self.configure(fg_color=("gray95", "gray10"))

        # --- Fade-In Window Effect ---
        self.attributes('-alpha', 0.0) # Start completely transparent
        self.after(100, self._fade_in) # Start fading in after a short delay

        # Create a main frame for the login elements, simulating a "glassy" card
        self.login_frame = ctk.CTkFrame(self,
                                        corner_radius=25,
                                        fg_color=("white", "gray15"),
                                        border_width=1,
                                        border_color=("gray80", "gray30"))
        self.login_frame.pack(pady=50, padx=50, fill="both", expand=True)

        # --- Profile Avatar ---
        # Create a placeholder image (you can replace this with a user's actual avatar)
        # Using a simple colored circle as a placeholder
        try:
            # Create a blank image for the circular avatar
            avatar_image_data = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            # Draw a circle on the image
            for x in range(100):
                for y in range(100):
                    if (x - 50)**2 + (y - 50)**2 < 50**2: # Check if point is within circle
                        avatar_image_data.putpixel((x, y), (74, 144, 226, 255)) # Blue color for avatar
            self.profile_avatar = ctk.CTkImage(light_image=avatar_image_data,
                                                dark_image=avatar_image_data,
                                                size=(80, 80)) # Size of the avatar
        except Exception as e:
            print(f"Error creating avatar image: {e}")
            # Fallback if PIL image creation fails
            self.profile_avatar = None

        if self.profile_avatar:
            self.avatar_label = ctk.CTkLabel(self.login_frame, image=self.profile_avatar, text="")
            self.avatar_label.pack(pady=(10, 10)) # Padding above the title

        # Login title with a clean font
        self.login_label = ctk.CTkLabel(self.login_frame,
                                        text="Access Your Account",
                                        font=ctk.CTkFont(size=28, weight="bold"))
        self.login_label.pack(pady=(10, 35)) # Adjusted padding after avatar

        # Username input with a clean, light appearance
        self.username_entry = ctk.CTkEntry(self.login_frame,
                                           placeholder_text="Username",
                                           width=300,
                                           height=45,
                                           corner_radius=15,
                                           font=ctk.CTkFont(size=15),
                                           fg_color=("gray90", "gray25"),
                                           border_color=("gray70", "gray40"),
                                           border_width=1)
        self.username_entry.pack(pady=12)
        # Focus styling for username entry
        self.username_entry.bind("<FocusIn>", lambda e: self.username_entry.configure(border_color="#4A90E2"))
        self.username_entry.bind("<FocusOut>", lambda e: self.username_entry.configure(border_color=("gray70", "gray40")))


        # Password input and show/hide toggle
        self.password_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        self.password_frame.pack(pady=12)

        self.password_entry = ctk.CTkEntry(self.password_frame,
                                           placeholder_text="Password",
                                           show="*", # Initially hide password characters
                                           width=300,
                                           height=45,
                                           corner_radius=15,
                                           font=ctk.CTkFont(size=15),
                                           fg_color=("gray90", "gray25"),
                                           border_color=("gray70", "gray40"),
                                           border_width=1)
        self.password_entry.pack(side="left", padx=(0, 5)) # Pack to the left
        # Focus styling for password entry
        self.password_entry.bind("<FocusIn>", lambda e: self.password_entry.configure(border_color="#4A90E2"))
        self.password_entry.bind("<FocusOut>", lambda e: self.password_entry.configure(border_color=("gray70", "gray40")))
        # Keyboard shortcut: Bind Return key to login_event when password field is active
        self.password_entry.bind("<Return>", lambda e: self.login_event())


        self.show_password_button = ctk.CTkButton(self.password_frame,
                                                  text="👁️", # Eye icon for show/hide
                                                  command=self.toggle_password_visibility,
                                                  width=45,
                                                  height=45,
                                                  corner_radius=15,
                                                  font=ctk.CTkFont(size=18),
                                                  fg_color=("gray70", "gray40"), # Match input field border color
                                                  hover_color=("gray60", "gray50"))
        self.show_password_button.pack(side="right") # Pack to the right

        self.password_visible = False # State to track password visibility

        # Feedback label (for both errors and success messages)
        self.feedback_label = ctk.CTkLabel(self.login_frame,
                                        text="",
                                        text_color="red", # Default to red for errors
                                        font=ctk.CTkFont(size=13, weight="bold"))
        self.feedback_label.pack(pady=(5, 0)) # Small padding below

        # Animated Loading Spinner (CTkProgressBar in indeterminate mode)
        self.loading_spinner = ctk.CTkProgressBar(self.login_frame,
                                                  mode="indeterminate",
                                                  width=300,
                                                  height=5,
                                                  corner_radius=5,
                                                  fg_color=("gray80", "gray30"),
                                                  progress_color="#4A90E2") # Match button color
        self.loading_spinner.pack(pady=(10, 0))
        self.loading_spinner.set(0) # Ensure it's empty initially
        self.loading_spinner.pack_forget() # Hide it initially

        # Login button with a clean, slightly transparent-looking blue
        self.login_button = ctk.CTkButton(self.login_frame,
                                          text="Log In",
                                          command=self.login_event,
                                          width=300,
                                          height=50,
                                          corner_radius=20,
                                          font=ctk.CTkFont(size=17, weight="bold"),
                                          fg_color="#4A90E2",
                                          hover_color="#357ABD")
        self.login_button.pack(pady=(20, 20)) # Adjusted padding

    def _fade_in(self):
        """Gradually increases the window opacity to create a fade-in effect."""
        alpha = self.attributes('-alpha')
        if alpha < 1.0:
            alpha += 0.05 # Increment opacity by 0.05
            self.attributes('-alpha', alpha)
            self.after(20, self._fade_in) # Call itself again after 20ms

    def toggle_password_visibility(self):
        """Toggles the visibility of the password in the entry field."""
        if self.password_visible:
            self.password_entry.configure(show="*") # Hide password
            self.show_password_button.configure(text="👁️")
            self.password_visible = False
        else:
            self.password_entry.configure(show="") # Show password
            self.show_password_button.configure(text="🔒") # Change icon to lock
            self.password_visible = True

    def login_event(self):
        """Handles the login button click event."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Clear any previous feedback messages
        self.feedback_label.configure(text="", text_color="red") # Reset color to default error

        # Show loading spinner and disable button
        self.loading_spinner.pack(pady=(10, 0)) # Show spinner
        self.loading_spinner.start() # Start indeterminate animation
        self.login_button.configure(text="Authenticating...", state="disabled")
        self.update_idletasks() # Update UI immediately

        # Simulate a network delay
        self.after(1500, lambda: self._process_login(username, password))

    def _process_login(self, username, password):
        """Processes the login attempt after a delay."""
        # Stop and hide loading spinner
        self.loading_spinner.stop()
        self.loading_spinner.pack_forget()

        if username == "user" and password == "password":
            self.feedback_label.configure(text="Login successful! Redirecting...", text_color="green")
            self.after(1000, self.destroy) # Close window after 1 second
        else:
            self.feedback_label.configure(text="Invalid username or password.", text_color="red")
            self.password_entry.delete(0, tk.END) # Clear password field for security
            self.after(3000, lambda: self.feedback_label.configure(text="")) # Hide error after 3 seconds

        # Reset button state
        self.login_button.configure(text="Log In", state="normal")


if __name__ == "__main__":
    app = App()
    app.mainloop()
