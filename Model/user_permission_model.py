class UserPermission:
    def __init__(self, user_id, permission_id):
        if user_id is None or permission_id is None:
            raise ValueError("Both User ID and Permission ID are required.")

        self.user_id = user_id
        self.permission_id = permission_id
