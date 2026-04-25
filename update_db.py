if __name__ == "__main__":
    print("HiddenEdge Engine v1.0 | SB3PM")
# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This code is proprietary and confidential.
# Unauthorized use, distribution, or replication is prohibited.
# =========================================

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