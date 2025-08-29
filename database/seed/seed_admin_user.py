import hashlib, sqlite3

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

conn = sqlite3.connect("weighbridge.db")
cur = conn.cursor()

# Step 1: Insert admin user
admin_username = "admin"
admin_password = "Weigh@2025"  # 🔑 Change as needed
hashed = hash_pw(admin_password)

try:
    cur.execute("INSERT INTO Users (Username, HashedPassword) VALUES (?, ?)", (admin_username, hashed))
    admin_id = cur.lastrowid
    print(f"✅ Admin created with ID {admin_id}")
except sqlite3.IntegrityError:
    cur.execute("SELECT Id FROM Users WHERE Username = ?", (admin_username,))
    admin_id = cur.fetchone()[0]
    print(f"ℹ️ Admin already exists (ID: {admin_id}), skipping insert")

# Step 2: Assign ALL permissions
cur.execute("SELECT Id FROM Permissions")
all_permission_ids = [row[0] for row in cur.fetchall()]

for perm_id in all_permission_ids:
    cur.execute("""
        INSERT OR IGNORE INTO UserPermissions (UserId, PermissionId)
        VALUES (?, ?)
    """, (admin_id, perm_id))

conn.commit()
conn.close()
print("✅ All permissions granted to admin.")
