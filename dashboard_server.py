from flask import Flask, request, jsonify
import stripe
import os
import sqlite3

app = Flask(__name__)

# =========================
# CONFIG
# =========================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DB_FILE = "subscriptions.db"

# =========================
# DB INIT
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            customer_id TEXT,
            subscription_id TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>HiddenEdge</title>
    </head>
    <body style="font-family:Arial;background:#0b1b3a;color:white;text-align:center;">

        <h1>Stop sending CVs that get ignored.</h1>

        <div style="margin-top:40px;">
            <input id="email" placeholder="Enter your email" style="padding:10px;width:300px;">
            <br><br>
            <button onclick="subscribe()">🚀 Unlock HiddenEdge</button>
        </div>

        <script>

        async function subscribe() {
            const email = document.getElementById("email").value;
            if (!email) {
                alert("Enter email");
                return;
            }

            localStorage.setItem("he_email", email);

            const res = await fetch("/create_checkout", {method:"POST"});
            const data = await res.json();

            window.location.href = data.url;
        }

        async function checkAccessWithRetry() {

            const email = localStorage.getItem("he_email");
            if (!email) return;

            for (let i = 0; i < 6; i++) {

                const res = await fetch("/check_access", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({email})
                });

                const data = await res.json();

                if (data.access) {

                    document.body.innerHTML = `
                        <h1>✅ ACCESS GRANTED</h1>
                        <button onclick="goApp()">Enter</button>
                    `;

                    window.goApp = function() {
                        window.location.href = "/app";
                    }

                    return;
                }

                await new Promise(r => setTimeout(r, 1500));
            }
        }

        checkAccessWithRetry();

        </script>

    </body>
    </html>
    """

# =========================
# CHECKOUT
# =========================

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": "price_1TKFETRsFYMAfQV15jNJ365D",
            "quantity": 1
        }],
        success_url=BASE_URL,
        cancel_url=BASE_URL
    )
    return jsonify({"url": session.url})

# =========================
# WEBHOOK (FIXED)
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        # ✅ FIXED ACCESS
        email = None

        if hasattr(session, "customer_details") and session.customer_details:
            email = session.customer_details.email

        if not email and hasattr(session, "customer_email"):
            email = session.customer_email

        print("💡 EMAIL FROM STRIPE:", email)

        subscription_id = session.subscription
        customer_id = session.customer

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("""
            INSERT INTO subscriptions (email, customer_id, subscription_id, status)
            VALUES (?, ?, ?, ?)
        """, (email, customer_id, subscription_id, "active"))

        conn.commit()
        conn.close()

        print("✅ USER STORED:", email)

    return "OK", 200

# =========================
# ACCESS CHECK
# =========================

@app.route("/check_access", methods=["POST"])
def check_access():
    data = request.json
    email = data.get("email")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT * FROM subscriptions
        WHERE email = ? AND status = 'active'
    """, (email,))

    result = c.fetchone()
    conn.close()

    return jsonify({"access": bool(result)})

# =========================
# APP
# =========================

@app.route("/app")
def app_entry():
    return "<h1>🚀 Welcome inside HiddenEdge</h1>"

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(port=5000, debug=True)