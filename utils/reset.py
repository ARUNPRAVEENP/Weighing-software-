import sqlite3

# Connect to the database
conn = sqlite3.connect("weighbridge.db")
cur = conn.cursor()

# 1️⃣ Update Admin Password
hashed_pw = "f64f7c19b83dfe93dfa4ab899a76978cbeefbc06a883b0136f486f081a44cd07"
cur.execute("""
    UPDATE Users 
    SET HashedPassword = ?
    WHERE Username = 'admin'
""", (hashed_pw,))
print("🔐 Admin password updated.")

# 2️⃣ Fetch admin user's ID
cur.execute("SELECT Id FROM Users WHERE Username = 'admin'")
admin_id = cur.fetchone()
if admin_id:
    admin_id = admin_id[0]
    print(f"👤 Admin User ID: {admin_id}")
else:
    print("❌ Admin user not found.")
    conn.close()
    exit()

# 3️⃣ Fetch all permission IDs
cur.execute("SELECT Id FROM Permissions")
permission_ids = [row[0] for row in cur.fetchall()]
print(f"📎 Found {len(permission_ids)} permissions.")

# 4️⃣ Insert all permissions for admin user (avoid duplicates)
for perm_id in permission_ids:
    cur.execute("""
        INSERT OR IGNORE INTO UserPermissions (UserId, PermissionId)
        VALUES (?, ?)
    """, (admin_id, perm_id))

conn.commit()
conn.close()

print("✅ Admin granted all permissions successfully.")

'''
import sqlite3
from resource_utils import resource_path

conn = sqlite3.connect("weighbridge.db")
try:
    conn.execute("ALTER TABLE WeighingTransactions ADD COLUMN Charges REAL;")
    print("Charges column added.")
except Exception as e:
    print(e)
conn.commit()
conn.close()'''