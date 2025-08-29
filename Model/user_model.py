class User:
    def __init__(self, id, username, hashed_password, permissions=None):
        if not username:
            raise ValueError("Username is required.")
        if not hashed_password:
            raise ValueError("Password hash is required.")

        self.id = id
        self.username = username
        self.hashed_password = hashed_password
        self.permissions = permissions or []  # List of Permission objects
