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

# ✅ FIX: dynamic base URL (works local + production)
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
# PAYWALL / HOME
# =========================

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>HiddenEdge</title>
        <style>
            body { margin:0; font-family: Arial; background:#0b1b3a; color:white; text-align:center; }
            .container { max-width:700px; margin:80px auto; }
            h1 { font-size:42px; }
            p { font-size:18px; color:#cfd8ff; }
            .box { margin-top:40px; background:#12275a; padding:30px; border-radius:10px; }
            button { background:#4ea3ff; border:none; padding:15px 25px; font-size:18px; border-radius:6px; cursor:pointer; margin-top:20px; }
            input { padding:10px; width:80%; margin-top:20px; border-radius:5px; border:none; }
            .checkbox { margin-top:15px; font-size:14px; color:#ccc; }
        </style>
    </head>
    <body>

        <div class="container">

            <h1>Stop sending CVs that get ignored.</h1>

            <p>
                HiddenEdge shows exactly why you're not getting interviews —
                and fixes your CV instantly.
            </p>

            <div class="box">

                <h2>€9 / month</h2>
                <p>Cancel anytime</p>

                <input id="email" placeholder="Enter your email" />

                <div class="checkbox">
                    <input type="checkbox" id="agree" />
                    I agree to immediate access and waive my right of withdrawal. All payments are non-refundable.
                </div>

                <button onclick="subscribe()">🚀 Unlock HiddenEdge</button>

            </div>

        </div>

        <script>
            async function subscribe() {

                const email = document.getElementById("email").value;
                const agree = document.getElementById("agree").checked;

                if (!email) {
                    alert("Enter your email");
                    return;
                }

                if (!agree) {
                    alert("You must accept the terms");
                    return;
                }

                localStorage.setItem("he_email", email);

                const res = await fetch("/create_checkout", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({email})
                });

                const data = await res.json();

                window.location.href = data.url;
            }

            async function checkAccess() {

                const email = localStorage.getItem("he_email");
                if (!email) return;

                const res = await fetch("/check_access", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({email})
                });

                const data = await res.json();

                if (data.access) {
                    document.body.innerHTML = `
                        <h1 style="margin-top:100px;">✅ Access Granted</h1>
                        <p>Welcome to HiddenEdge.</p>
                    `;
                }
            }

            checkAccess();
        </script>

    </body>
    </html>
    """

# -------------------------
# CREATE CHECKOUT
# -------------------------
@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    data = request.get_json()
    email = data.get("email")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=email,
        line_items=[{
            "price": "price_1TKFETRsFYMAfQV15jNJ365D",
            "quantity": 1
        }],
        success_url=f"{BASE_URL}",
        cancel_url=f"{BASE_URL}"
    )

    return jsonify({"url": session.url})

# -------------------------
# WEBHOOK
# -------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        print("Webhook error:", e)
        return "Invalid", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        email = session.get("customer_details", {}).get("email") or session.get("customer_email")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")

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

# -------------------------
# CHECK ACCESS
# -------------------------
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
# RUN
# =========================

if __name__ == "__main__":
    app.run(port=5000, debug=True)