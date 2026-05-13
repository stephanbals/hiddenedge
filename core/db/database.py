import os
import psycopg2
import traceback


# =========================================
# DATABASE
# =========================================

def get_db():

    return psycopg2.connect(
        os.getenv("DATABASE_URL")
    )


# =========================================
# INIT DATABASE
# =========================================

def init_db():

    try:

        conn = get_db()

        cur = conn.cursor()

        # =========================================
        # USERS
        # =========================================

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id SERIAL PRIMARY KEY,

            email TEXT UNIQUE,

            free_uses INTEGER
            DEFAULT 0,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =========================================
        # SUBSCRIPTIONS
        # =========================================

        cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (

            id SERIAL PRIMARY KEY,

            email TEXT,

            stripe_customer_id TEXT,

            stripe_subscription_id TEXT UNIQUE,

            status TEXT,

            plan TEXT,

            cancel_at_period_end BOOLEAN
            DEFAULT FALSE,

            current_period_end TIMESTAMP,

            created_at TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =========================================
        # SAFE MIGRATION
        # =========================================

        try:

            cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS free_uses INTEGER DEFAULT 0
            """)

        except Exception as migration_error:

            print(
                "[MIGRATION WARNING]",
                migration_error
            )

        conn.commit()

        cur.close()
        conn.close()

        print(
            "[DB] initialization complete"
        )

    except Exception as e:

        print(
            "[DB INIT ERROR]",
            e
        )

        traceback.print_exc()