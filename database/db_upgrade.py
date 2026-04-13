import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "jobs.db")


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def add_column(cursor, table, column, column_type):
    print(f"Adding column: {column}")
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def upgrade_database():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    upgrades = [
        ("source", "TEXT"),
        ("location", "TEXT"),
        ("rate_min", "INTEGER"),
        ("rate_max", "INTEGER"),
        ("status", "TEXT"),
        ("notes", "TEXT"),
        ("applied_date", "TEXT"),
        ("followup_date", "TEXT"),
        ("duplicate_hash", "TEXT")
    ]

    for column, column_type in upgrades:
        if not column_exists(cursor, "opportunities", column):
            add_column(cursor, "opportunities", column, column_type)

    conn.commit()
    conn.close()

    print("Database upgrade completed.")


if __name__ == "__main__":
    upgrade_database()