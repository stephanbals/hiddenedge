
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 🔥 ENSURE ENV IS LOADED HERE
load_dotenv()

def get_connection():
    url = os.getenv("DATABASE_URL")

    if not url:
        print("❌ DATABASE_URL NOT FOUND")
        return None

    print("DB CONNECT USING:", url)  # 🔥 DEBUG

    return psycopg2.connect(url)


# =========================================
# INIT DB (SAFE, NO REGRESSION)
# =========================================

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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscription_start TIMESTAMP,
        subscription_end TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ DB initialized")


# =========================================
# USER HANDLING
# =========================================

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
        "INSERT INTO users (email, subscription_status) VALUES (%s, 'free') RETURNING *",
        (email,)
    )
    user = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return user


# =========================================
# 🔥 SET USER PAID — FIXED (30-DAY LOGIC)
# =========================================

def set_user_paid(email):
    conn = get_connection()
    if not conn:
        return

    cur = conn.cursor()

    now = datetime.utcnow()
    end = now + timedelta(days=30)

    cur.execute("""
        UPDATE users
        SET 
            subscription_status = 'active',
            subscription_start = %s,
            subscription_end = %s
        WHERE email = %s
    """, (now, end, email))

    conn.commit()
    cur.close()
    conn.close()

    print("✅ USER ACTIVATED:", email)