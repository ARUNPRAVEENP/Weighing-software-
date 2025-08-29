import customtkinter as ctk
from ui.login_window import LoginWindow
from ui.main_dashboard_window import MainDashboardFrame

class App(ctk.CTk):
    """
    This is the single root window for the entire application.
    """
    def __init__(self):
        super().__init__()

        # Hide the root window completely at the start.
        self.withdraw()

        self.title("Weighbridge App")
        self.geometry("1100x700")

        # Run the login flow. The app will wait here until the login window is closed.
        if self.show_login_window():
            # If login was successful, build the main dashboard
            self.setup_dashboard()
            # Now, make the fully-built main window visible.
            self.deiconify()
        else:
            # If login failed or was cancelled, destroy the app.
            self.destroy()

    def show_login_window(self):
        """Creates and shows the modal login window."""
        login = LoginWindow(self)
        self.wait_window(login) # This pauses the code here until login.destroy() is called
        return login.is_successful

    def setup_dashboard(self):
        """Configures the root window grid and places the dashboard frame inside it."""
        # Configure the grid layout to allow the dashboard frame to fill the window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create an instance of your dashboard frame
        dashboard = MainDashboardFrame(self)
        
        # Place the dashboard frame in the grid. This is the stable way to do it.
        dashboard.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    app = App()
    app.mainloop()