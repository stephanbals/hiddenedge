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
            customer_id TEXT,
            subscription_id TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# HOME (PAYWALL)
# =========================

@app.route("/")
def home():
    return '''
    <html>
    <body style="font-family:Arial;background:#0b1b3a;color:white;text-align:center;">

        <h1>HiddenEdge</h1>

        <button onclick="subscribe()">Unlock</button>

        <div id="debug" style="margin-top:20px;color:yellow;"></div>

        <script>

        const urlParams = new URLSearchParams(window.location.search);
        const justPaid = urlParams.get("success");

        async function subscribe() {
            const res = await fetch("/create_checkout", {
                method: "POST"
            });
            const data = await res.json();
            window.location.href = data.url;
        }

        async function checkAccessWithRetry(customer_id) {

            for (let i = 0; i < 10; i++) {

                const res = await fetch("/check_access", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({customer_id})
                });

                const data = await res.json();

                if (data.access) {
                    window.location.href = "/app";
                    return;
                }

                await new Promise(r => setTimeout(r, 1500));
            }

            document.getElementById("debug").innerText = "Access failed after retries";
        }

        if (justPaid) {

            const session_id = urlParams.get("session_id");

            fetch("/get_session?session_id=" + session_id)
                .then(r => r.json())
                .then(data => {
                    localStorage.setItem("he_customer_id", data.customer_id);
                    checkAccessWithRetry(data.customer_id);
                });
        }

        </script>

    </body>
    </html>
    '''

# =========================
# STRIPE CHECKOUT
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
        success_url=BASE_URL + "?success=1&session_id={CHECKOUT_SESSION_ID}",
        cancel_url=BASE_URL
    )

    return jsonify({"url": session.url})

# =========================
# GET SESSION (for customer_id)
# =========================

@app.route("/get_session")
def get_session():
    session_id = request.args.get("session_id")
    session = stripe.checkout.Session.retrieve(session_id)

    return jsonify({
        "customer_id": session.customer
    })

# =========================
# WEBHOOK
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

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("""
            INSERT INTO subscriptions (customer_id, subscription_id, status)
            VALUES (?, ?, ?)
        """, (session.customer, session.subscription, "active"))

        conn.commit()
        conn.close()

        print("USER STORED:", session.customer)

    return "OK", 200

# =========================
# ACCESS CHECK
# =========================

@app.route("/check_access", methods=["POST"])
def check_access():
    data = request.json
    customer_id = data.get("customer_id")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT * FROM subscriptions
        WHERE customer_id = ? AND status = 'active'
    """, (customer_id,))

    result = c.fetchone()
    conn.close()

    return jsonify({"access": bool(result)})

# =========================
# APP (YOUR PRODUCT UI)
# =========================

@app.route("/app")
def app_entry():
    return """
    <html>
    <body style="font-family:Arial;background:#0b1b3a;color:white;padding:40px;">

        <h1>🚀 HiddenEdge</h1>

        <h3>Paste your CV:</h3>
        <textarea id="cv" rows="10" cols="80"></textarea>

        <h3>Paste Job Description:</h3>
        <textarea id="job" rows="10" cols="80"></textarea>

        <br><br>
        <button onclick="analyze()">Analyze</button>

        <pre id="result"></pre>

        <script>

        async function analyze() {

            const cv = document.getElementById("cv").value;
            const job = document.getElementById("job").value;

            const res = await fetch("/analyze", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({cv, job})
            });

            const data = await res.json();

            document.getElementById("result").innerText = data.result;
        }

        </script>

    </body>
    </html>
    """

# =========================
# ANALYZE (TEMP LOGIC)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    cv = data.get("cv", "")
    job = data.get("job", "")

    result = f"Analysis result:\\n\\nCV length: {len(cv)}\\nJob length: {len(job)}"

    return jsonify({"result": result})

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(port=5000, debug=True)