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
# HOME / PAYWALL
# =========================

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>HiddenEdge</title>
    </head>
    <body style="background:#0b1b3a;color:white;text-align:center;font-family:Arial;">

        <h1>Stop sending CVs that get ignored.</h1>

        <p>HiddenEdge shows exactly why you're not getting interviews — and fixes your CV instantly.</p>

        <h2>€9 / month</h2>

        <input id="email" placeholder="Enter your email" />
        <br><br>

        <button onclick="subscribe()">🚀 Unlock HiddenEdge</button>

        <script>
            async function subscribe() {

                const email = document.getElementById("email").value;

                if (!email) {
                    alert("Enter email");
                    return;
                }

                localStorage.setItem("he_email", email);

                const res = await fetch("/create_checkout", { method: "POST" });
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
                        <h1>✅ ACCESS GRANTED</h1>
                    `;
                }
            }

            checkAccess();
        </script>

    </body>
    </html>
    """

# =========================
# CREATE CHECKOUT
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
        success_url=BASE_URL + "/success",
        cancel_url=BASE_URL
    )
    return jsonify({"url": session.url})

# =========================
# SUCCESS PAGE (TEST MODE)
# =========================

@app.route("/success")
def success():
    email = request.args.get("email")

    # fallback to localStorage approach if missing
    if not email:
        return """
        <script>
            const email = localStorage.getItem("he_email");
            fetch("/force_grant", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({email})
            }).then(() => {
                window.location.href = "/";
            });
        </script>
        """

    return "Success"

# =========================
# FORCE GRANT ACCESS (TEST)
# =========================

@app.route("/force_grant", methods=["POST"])
def force_grant():
    data = request.json
    email = data.get("email")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        INSERT INTO subscriptions (email, customer_id, subscription_id, status)
        VALUES (?, ?, ?, ?)
    """, (email, "test_customer", "test_sub", "active"))

    conn.commit()
    conn.close()

    print("🔥 FORCE ACCESS GRANTED:", email)

    return jsonify({"ok": True})

# =========================
# WEBHOOK (UNCHANGED)
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        email = session.get("customer_details", {}).get("email")

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

# =========================
# CHECK ACCESS
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
# RUN
# =========================

if __name__ == "__main__":
    app.run(port=5000, debug=True)