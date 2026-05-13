import traceback

from core.db.database import get_db


# =========================================
# SUBSCRIPTION LOOKUP
# =========================================

def get_subscription_by_email(email):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        SELECT
            email,
            status,
            plan,
            current_period_end

        FROM subscriptions

        WHERE email = %s

        ORDER BY created_at DESC

        LIMIT 1

        """, (email,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return None

        return {

            "email": row[0],
            "status": row[1],
            "plan": row[2],
            "current_period_end": row[3]
        }

    except Exception as e:

        print(
            "[SUB LOOKUP ERROR]",
            e
        )

        return None


# =========================================
# USER USAGE
# =========================================

def get_user_free_uses(email):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        SELECT free_uses

        FROM users

        WHERE email = %s

        """, (email,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:
            return 0

        return row[0] or 0

    except Exception as e:

        print(
            "[FREE USE LOOKUP ERROR]",
            e
        )

        return 0


def increment_user_free_uses(email):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        UPDATE users

        SET free_uses = free_uses + 1

        WHERE email = %s

        """, (email,))

        conn.commit()

        cur.close()
        conn.close()

        print(
            f"[FREE USE INCREMENTED] {email}"
        )

    except Exception as e:

        print(
            "[FREE USE INCREMENT ERROR]",
            e
        )

        traceback.print_exc()


# =========================================
# SAVE SUBSCRIPTION
# =========================================

def save_subscription(

    email,
    customer_id,
    subscription_id,
    status,
    plan,
    current_period_end

):

    try:

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        INSERT INTO subscriptions (

            email,
            stripe_customer_id,
            stripe_subscription_id,
            status,
            plan,
            current_period_end

        )

        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,

            CASE
                WHEN %s IS NOT NULL
                THEN to_timestamp(%s)
                ELSE NULL
            END
        )

        ON CONFLICT (
            stripe_subscription_id
        )

        DO UPDATE SET

            status = EXCLUDED.status,

            current_period_end =
                EXCLUDED.current_period_end

        """, (

            email,
            customer_id,
            subscription_id,
            status,
            plan,

            current_period_end,
            current_period_end

        ))

        conn.commit()

        cur.close()
        conn.close()

        print(
            f"[SUBSCRIPTION SAVED] {email}"
        )

    except Exception as e:

        print(
            "[SAVE SUB ERROR]",
            e
        )

        traceback.print_exc()