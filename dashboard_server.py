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

        <h1>HiddenEdge</h1>

        <button onclick="subscribe()">Unlock</button>

        <div id="debug" style="margin-top:20px;color:yellow;"></div>

        <script>

        const urlParams = new URLSearchParams(window.location.search);
        const justPaid = urlParams.get("success");

        function log(msg) {
            document.getElementById("debug").innerHTML += "<br>" + msg;
        }

        async function subscribe() {

            const res = await fetch("/create_checkout", {
                method: "POST"
            });

            const data = await res.json();
            window.location.href = data.url;
        }

        async function checkAccessWithRetry() {

            const customer_id = localStorage.getItem("he_customer_id");

            log("Checking customer_id: " + customer_id);

            for (let i = 0; i < 10; i++) {

                const res = await fetch("/check_access", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({customer_id})
                });

                const data = await res.json();

                log("Attempt " + i + " → " + JSON.stringify(data));

                if (data.access) {
                    document.body.innerHTML = "<h1>ACCESS GRANTED</h1>";
                    return;
                }

                await new Promise(r => setTimeout(r, 1500));
            }

            log("FAILED");
        }

        if (justPaid) {
            log("Payment detected");

            // 🔥 GET SESSION TO EXTRACT CUSTOMER ID
            fetch("/get_session")
                .then(r => r.json())
                .then(data => {
                    localStorage.setItem("he_customer_id", data.customer_id);
                    checkAccessWithRetry();
                });
        }

        </script>

    </body>
    </html>
    '''

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


@app.route("/get_session")
def get_session():
    session_id = request.args.get("session_id")

    session = stripe.checkout.Session.retrieve(session_id)

    return jsonify({
        "customer_id": session.customer
    })


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


if __name__ == "__main__":
    app.run(port=5000, debug=True)