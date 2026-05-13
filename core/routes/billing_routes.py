from flask import (
    Blueprint,
    request,
    jsonify
)

import traceback

from core.stripe.stripe_service import (
    handle_success,
    create_checkout_session
)

from core.db.database import get_db

billing_routes = Blueprint(
    "billing_routes",
    __name__
)

# =========================================
# STRIPE SUCCESS
# =========================================

@billing_routes.route("/success")
def success():

    session_id = request.args.get(
        "session_id"
    )

    return handle_success(session_id)

# =========================================
# STRIPE CUSTOMER PORTAL
# =========================================

@billing_routes.route(
    "/create-customer-portal-session",
    methods=["POST"]
)
def create_customer_portal():

    try:

        data = request.get_json()

        email = data.get("email")

        if not email:

            return jsonify({
                "error": "Missing email"
            }), 400

        conn = get_db()

        cur = conn.cursor()

        cur.execute("""

        SELECT stripe_customer_id

        FROM subscriptions

        WHERE email = %s

        ORDER BY created_at DESC

        LIMIT 1

        """, (email,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row:

            return jsonify({
                "error": "No subscription found"
            }), 404

        stripe_customer_id = row[0]

        import stripe

        session = stripe.billing_portal.Session.create(

            customer=stripe_customer_id,

            return_url="http://127.0.0.1:5000/app"
        )

        return jsonify({
            "url": session.url
        })

    except Exception as e:

        print(
            "[CUSTOMER PORTAL ERROR]",
            e
        )

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# STRIPE CHECKOUT
# =========================================

@billing_routes.route(
    "/create-checkout-session",
    methods=["POST"]
)
def create_checkout():

    try:

        data = request.get_json(
            silent=True
        )

        customer_email = None

        if data and isinstance(data, dict):

            customer_email = data.get(
                "email"
            )

        if not customer_email:

            customer_email = request.form.get(
                "email"
            )

        if not customer_email:

            customer_email = request.args.get(
                "email"
            )

        if not customer_email:

            return jsonify({
                "error": "Missing email"
            }), 400

        checkout = create_checkout_session(
            customer_email
        )

        return jsonify({
            "url": checkout.url
        })

    except Exception as e:

        print("STRIPE ERROR:", e)

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500