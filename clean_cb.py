import sqlite3

conn = sqlite3.connect("database/jobs.db")
cursor = conn.cursor()

cursor.execute("""
DELETE FROM opportunities
WHERE url IS NULL
   OR url = ''
   OR url NOT LIKE 'http%'
""")

conn.commit()
conn.close()

print("✅ Database cleaned")