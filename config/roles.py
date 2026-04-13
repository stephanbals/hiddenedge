import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "jobs.db")


DEFAULT_ROLES = [

    "program manager",
    "transformation manager",
    "it project manager",
    "sap project manager",
    "agile coach",
    "scrum master",
    "product owner",
    "pmo lead"

]


def init_roles():

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT UNIQUE,
        active INTEGER
    )
    """)

    conn.commit()

    for r in DEFAULT_ROLES:

        cursor.execute(
            "INSERT OR IGNORE INTO roles(role,active) VALUES(?,1)",
            (r,)
        )

    conn.commit()
    conn.close()


def get_active_roles():

    # ensure table exists before reading
    init_roles()

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT role FROM roles WHERE active=1")

    rows = cursor.fetchall()

    conn.close()

    return [r[0] for r in rows]