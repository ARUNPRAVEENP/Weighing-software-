import hashlib
from repositories.user_repository import UserRepository

class UserManagementViewModel:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.user_list = []
        self.available_permissions = []
        self.refresh_data()

    def refresh_data(self):
        self.user_list = self.user_repo.get_all_users()
        self.available_permissions = self.user_repo.get_all_permissions()

    def add_user(self, username, password):
        self.user_repo.add_user(username, password)
        self.refresh_data()

    def edit_user(self, user_id, updated_username):
        result = self.user_repo.update_username(user_id, updated_username)
        self.refresh_data()
        return result

    def delete_user(self, user_id):
        result = self.user_repo.delete_user(user_id)
        self.refresh_data()
        return result

    def assign_permissions(self, username, permission_names):
        user = self.user_repo.get_user_by_username(username)
        if user:
            return self.user_repo.update_user_permissions(user.id, permission_names)

    def update_user_password(self, user_id, new_password):
        self.user_repo.update_password(user_id, new_password)

    def get_permissions_for_user(self, username):
        user = self.user_repo.get_user_by_username(username)
        if user:
            return self.user_repo.get_permissions_by_user(user.id)
        return []

    def get_user_id_by_username(self, username):
        user = self.user_repo.get_user_by_username(username)
        return user.id if user else None
    # In your UserManagementViewModel
    def delete_user_by_id(self, user_id):
        self.user_repo.delete_user_by_id(user_id)
