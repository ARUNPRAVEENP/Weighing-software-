import sqlite3
from resource_utils import resource_path


DB_NAME = "weighbridge.db"
SCHEMA_FOLDER = "database/schema"
SEED_FOLDER = "database/seed"

def run_sql_scripts_from(folder):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".sql"):
            path = os.path.join(folder, filename)
            print(f"⏳ Running: {filename}")
            with open(path, "r", encoding="utf-8") as f:
                sql_script = f.read()
                try:
                    cursor.executescript(sql_script)
                    print(f"✅ Success: {filename}")
                except Exception as e:
                    print(f"❌ Failed: {filename}\n   Reason: {e}")
    
    conn.commit()
    conn.close()

def initialize_database():
    if not os.path.exists(DB_NAME):
        print(f"📦 Creating new database file: {DB_NAME}")
    else:
        print(f"🗃️ Updating existing database: {DB_NAME}")

    print("\n📐 Applying schema...")
    run_sql_scripts_from(SCHEMA_FOLDER)

    print("\n🌱 Seeding data...")
    run_sql_scripts_from(SEED_FOLDER)

    print("\n🎉 Database initialization complete!")

if __name__ == "__main__":
    initialize_database()