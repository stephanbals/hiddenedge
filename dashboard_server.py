from flask import Flask, request, jsonify
import stripe
import os
import sqlite3

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DB_FILE = "subscriptions.db"

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

@app.route("/")
def home():
    return '''
    <html>
    <body style="font-family:Arial;background:#0b1b3a;color:white;text-align:center;">

        <h1>HiddenEdge Debug Mode</h1>

        <input id="email" placeholder="Enter your email">
        <br><br>
        <button onclick="subscribe()">Unlock</button>

        <div id="debug" style="margin-top:20px;color:yellow;"></div>

        <script>

        const urlParams = new URLSearchParams(window.location.search);
        const justPaid = urlParams.get("success");

        function log(msg) {
            document.getElementById("debug").innerHTML += "<br>" + msg;
        }

        async function subscribe() {

            const email = document.getElementById("email").value;

            if (!email) {
                alert("Enter email");
                return;
            }

            localStorage.setItem("he_email", email);
            log("Saved email: " + email);

            const res = await fetch("/create_checkout", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({email: email})
            });

            const data = await res.json();
            window.location.href = data.url;
        }

        async function checkAccessWithRetry() {

            const email = localStorage.getItem("he_email");

            log("Checking access for: " + email);

            for (let i = 0; i < 10; i++) {

                const res = await fetch("/check_access", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({email})
                });

                const data = await res.json();

                log("Attempt " + i + " → " + JSON.stringify(data));

                if (data.access) {
                    document.body.innerHTML = "<h1>ACCESS GRANTED</h1>";
                    return;
                }

                await new Promise(r => setTimeout(r, 1500));
            }

            log("FAILED: No access after retries");
        }

        if (justPaid) {
            log("Payment detected");
            checkAccessWithRetry();
        }

        </script>

    </body>
    </html>
    '''

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    data = request.json
    email = data.get("email")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": "price_1TKFETRsFYMAfQV15jNJ365D",
            "quantity": 1
        }],
        success_url=BASE_URL + "?success=1",
        cancel_url=BASE_URL,
        customer_email=email,
        metadata={"email": email}
    )

    return jsonify({"url": session.url})

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
        email = session.metadata.get("email")

        print("WEBHOOK EMAIL:", email)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("""
            INSERT INTO subscriptions (email, customer_id, subscription_id, status)
            VALUES (?, ?, ?, ?)
        """, (email, session.customer, session.subscription, "active"))

        conn.commit()
        conn.close()

        print("USER STORED:", email)

    return "OK", 200

@app.route("/check_access", methods=["POST"])
def check_access():
    data = request.json
    email = data.get("email")

    print("CHECK ACCESS FOR:", email)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT * FROM subscriptions
        WHERE email = ? AND status = 'active'
    """, (email,))

    result = c.fetchone()
    conn.close()

    print("RESULT:", result)

    return jsonify({"access": bool(result)})

if __name__ == "__main__":
    app.run(port=5000, debug=True)