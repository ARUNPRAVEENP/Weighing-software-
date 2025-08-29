import sqlite3
import hashlib
from resource_utils import resource_path


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class User:
    def __init__(self, id, username, hashed_password):
        self.id = id
        self.username = username
        self.hashed_password = hashed_password

class UserRepository:
    def __init__(self, db_path="weighbridge.db"):
        self.db_path = resource_path(db_path)

    def connect(self):
        return sqlite3.connect(self.db_path)

    def get_user_by_username(self, username):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT Id, Username, HashedPassword FROM Users WHERE Username = ?", (username,))
            row = cur.fetchone()
            return User(*row) if row else None

    def verify_password(self, stored_hash, input_password):
        hashed_input = hash_password(input_password)
        return hashed_input == stored_hash

    def get_permissions_by_user(self, user_id):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.Name FROM Permissions p
                JOIN UserPermissions up ON up.PermissionId = p.Id
                WHERE up.UserId = ?
            """, (user_id,))
            return [row[0] for row in cur.fetchall()]

    def get_all_username(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT Username FROM Users ORDER BY Username")
            return [row[0] for row in cur.fetchall()]

    def get_all_users(self):
        return self.get_all_username()

    def get_all_permissions(self):
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT Name FROM Permissions")
            return [row[0] for row in cur.fetchall()]

    def add_user(self, username, password):
        hashed_pw = hash_password(password)
        with self.connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO Users (Username, HashedPassword) VALUES (?, ?)", (username, hashed_pw))
                conn.commit()
                print(f"✅ Created user '{username}'")
                return True
            except sqlite3.IntegrityError:
                print(f"⚠️ Username '{username}' already exists.")
                return False

    def delete_user(self, user_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM Users WHERE Id = ?", (user_id,))
            conn.commit()

    def update_user_permissions(self, user_id, permission_names):
        if not isinstance(user_id, int):
            raise ValueError(f"user_id must be an integer, got {type(user_id)}")

        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM UserPermissions WHERE UserId = ?", (user_id,))

            if permission_names:
                placeholders = ','.join('?' for _ in permission_names)
                cur.execute(f"SELECT Id, Name FROM Permissions WHERE Name IN ({placeholders})", permission_names)
                name_to_id = {name: pid for pid, name in cur.fetchall()}
                insert_data = [(user_id, name_to_id[name]) for name in permission_names if name in name_to_id]
                cur.executemany("INSERT INTO UserPermissions (UserId, PermissionId) VALUES (?, ?)", insert_data)

            conn.commit()

    def update_password(self, user_id, new_password):
        hashed = hash_password(new_password)
        with self.connect() as conn:
            conn.execute("UPDATE Users SET HashedPassword = ? WHERE Id = ?", (hashed, user_id))
            conn.commit()

    def update_username(self, user_id, new_username):
        with self.connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute("UPDATE Users SET Username = ? WHERE Id = ?", (new_username, user_id))
                conn.commit()
                print(f"✏️ Username updated to '{new_username}' for user ID {user_id}")
                return True
            except sqlite3.IntegrityError:
                print(f"⚠️ Username '{new_username}' already exists.")
                return False

    def delete_user_by_id(self, user_id):
        self.delete_user(user_id)