class Permission:
    def __init__(self, id, name, description=None):
        if not name:
            raise ValueError("Permission name is required.")

        self.id = id
        self.name = name
        self.description = description
