import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        return None
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    if not conn:
        print("⚠ No DATABASE_URL set")
        return

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        stripe_customer_id TEXT,
        subscription_status TEXT DEFAULT 'free',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ DB initialized")

def get_or_create_user(email):
    conn = get_connection()
    if not conn:
        return None

    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    if user:
        cur.close()
        conn.close()
        return user

    cur.execute(
        "INSERT INTO users (email) VALUES (%s) RETURNING *",
        (email,)
    )
    user = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return user

def set_user_paid(email):
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET subscription_status = 'active' WHERE email = %s",
        (email,)
    )

    conn.commit()
    cur.close()
    conn.close()