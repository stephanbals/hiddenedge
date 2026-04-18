import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# STRIPE CONFIG (ENV BASED)
# =========================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Temporary in-memory storage (replace later with DB)
paid_users = set()

# =========================
# HEALTH CHECK
# =========================

@app.route("/", methods=["GET"])
def home():
    return "HiddenEdge Backend Running"


# =========================
# CREATE CHECKOUT SESSION
# =========================

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "Missing email"}), 400

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=email,
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url="https://hiddenedge-live.onrender.com/app?paid=true",
            cancel_url="https://hiddenedge-live.onrender.com/app?canceled=true",
        )

        return jsonify({"url": session.url})

    except Exception as e:
        print("CHECKOUT ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# =========================
# WEBHOOK
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print("Webhook signature error:", str(e))
        return "", 400

    # =========================
    # HANDLE EVENTS
    # =========================

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")

        if email:
            print(f"✅ Payment success for: {email}")
            paid_users.add(email)

    return "", 200


# =========================
# CHECK IF USER IS PAID
# =========================

@app.route("/check_payment", methods=["POST"])
def check_payment():
    data = request.get_json()
    email = data.get("email")

    if email in paid_users:
        return jsonify({"paid": True})

    return jsonify({"paid": False})


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)