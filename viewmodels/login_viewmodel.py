# viewmodels/login_viewmodel.py
from repositories.user_repository import UserRepository

class LoginViewModel:
    def __init__(self, user_repo):
        self.username = ""
        self.password = ""
        self.error_message = ""
        self.logged_in_user = None
        self.user_permissions = []
        self.user_repo = user_repo
        self.is_logged_in = False  # <--- ADDED THIS FLAG

    def login(self):
        self.error_message = ""  # Clear previous errors
        self.is_logged_in = False  # Reset login status for new attempt

        if not self.username or not self.password:
            self.error_message = "Username and password cannot be empty."
            return False

        user = self.user_repo.get_user_by_username(self.username)
        if not user:
            self.error_message = "User not found"
            return False

        # Assuming user.hashed_password exists and verify_password works
        if not self.user_repo.verify_password(user.hashed_password, self.password):
            self.error_message = "Incorrect password"
            return False

        self.logged_in_user = user
        self.user_permissions = self.user_repo.get_permissions_by_user(user.id)
        self.is_logged_in = True  # <--- SET TO TRUE ON SUCCESSFUL LOGIN
        return True

    def has_permission(self, permission_name):
        return permission_name in self.user_permissions

# The following lines are for example/testing purposes,
# and should generally not be in the final class definition if it's imported.
# user_repo = UserRepository()
# vm = LoginViewModel(user_repo)