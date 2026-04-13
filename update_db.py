import sqlite3

DB_PATH = "jobs.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE jobs ADD COLUMN score INTEGER DEFAULT 0;")
    print("✅ Column 'score' added successfully.")
except Exception as e:
    print("⚠️ Possibly already exists:", e)

conn.commit()
conn.close()