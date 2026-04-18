import os
import stripe
from flask import Flask, request, jsonify, render_template

# ------------------------
# CONFIG
# ------------------------

app = Flask(__name__, template_folder="templates")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL")

if not STRIPE_SECRET_KEY:
    raise ValueError("Missing STRIPE_SECRET_KEY")

if not STRIPE_PRICE_ID:
    raise ValueError("Missing STRIPE_PRICE_ID")

stripe.api_key = STRIPE_SECRET_KEY

# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def home():
    # 🔥 Serve frontend instead of plain text
    return render_template("index.html")


@app.route("/app")
def app_page():
    return render_template("index.html")


# ------------------------
# ANALYZE ENDPOINT
# ------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        cv_text = data.get("cv_text")
        job_description = data.get("job_description")

        if not cv_text or not job_description:
            return jsonify({"error": "Missing input"}), 400

        # Temporary placeholder logic
        score = 85
        decision = "Strong Match"

        return jsonify({
            "score": score,
            "decision": decision
        })

    except Exception as e:
        print("❌ Analyze error:", str(e))
        return jsonify({"error": "Analyze failed"}), 500


# ------------------------
# STRIPE CHECKOUT
# ------------------------

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    try:
        if not BASE_URL:
            return jsonify({"error": "Missing BASE_URL"}), 500

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{BASE_URL}/app?success=true",
            cancel_url=f"{BASE_URL}/app?canceled=true",
        )

        return jsonify({"url": session.url})

    except Exception as e:
        print("❌ Stripe checkout error:", str(e))
        return jsonify({"error": "Checkout failed"}), 500


# ------------------------
# STRIPE WEBHOOK
# ------------------------

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print("❌ Webhook signature error:", str(e))
        return "", 400

    # Handle event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        print("✅ Payment successful:", session.get("customer_email"))

    return "", 200


# ------------------------
# HEALTH CHECK (useful for debugging)
# ------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ------------------------
# RUN
# ------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)