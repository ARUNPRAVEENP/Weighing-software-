from datetime import datetime

class AuditLog:
    def __init__(self, id, action_type, description,
                 timestamp=None, user_id=None, affected_record_id=None,
                 table_name=None, old_value=None, new_value=None, ip_address=None):
        
        if not action_type:
            raise ValueError("Action type is required.")
        if not description:
            raise ValueError("Description is required.")
        
        self.id = id                                # Primary Key
        self.user_id = user_id                      # FK to User, nullable
        self.action_type = action_type              # e.g., "Login", "PermissionChanged"
        self.description = description              # What happened, in text
        self.timestamp = timestamp or datetime.now()  # Defaults to now
        self.affected_record_id = affected_record_id
        self.table_name = table_name
        self.old_value = old_value                  # JSON string (optional)
        self.new_value = new_value                  # JSON string (optional)
        self.ip_address = ip_address
