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
DB_FILE = "app.db"

FREE_LIMIT = 3

# =========================
# DB INIT
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            usage_count INTEGER DEFAULT 0,
            customer_id TEXT,
            subscription_status TEXT,
            eula_accepted INTEGER DEFAULT 0
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
    return '''
    <html>
    <body style="margin:0;font-family:Arial;background:#0b1b3a;color:white;display:flex;justify-content:center;align-items:center;height:100vh;">

        <div style="text-align:center;">
            <h1 style="font-size:42px;">HiddenEdge</h1>
            <p style="color:#cfd8ff;">AI-powered CV decision engine</p>

            <input id="email" placeholder="your@email.com"
                   style="padding:12px;width:280px;border-radius:6px;border:none;margin-top:20px;">
            <br><br>
            <button onclick="start()"
                    style="padding:12px 24px;background:#4ea3ff;border:none;border-radius:6px;color:white;font-size:16px;cursor:pointer;">
                Start
            </button>
        </div>

        <script>
        function start() {
            const email = document.getElementById("email").value;

            if (!email) {
                alert("Enter email");
                return;
            }

            localStorage.setItem("he_email", email);
            window.location.href = "/app";
        }
        </script>

    </body>
    </html>
    '''

# =========================
# EULA
# =========================

@app.route("/check_eula", methods=["POST"])
def check_eula():
    email = request.json.get("email")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT eula_accepted FROM users WHERE email = ?", (email,))
    row = c.fetchone()

    if not row:
        c.execute("INSERT INTO users (email) VALUES (?)", (email,))
        conn.commit()
        accepted = 0
    else:
        accepted = row[0]

    conn.close()

    return jsonify({"accepted": bool(accepted)})

@app.route("/accept_eula", methods=["POST"])
def accept_eula():
    email = request.json.get("email")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("UPDATE users SET eula_accepted = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})

# =========================
# STRIPE
# =========================

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    email = request.json.get("email")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=email,
        line_items=[{
            "price": "price_1TKFETRsFYMAfQV15jNJ365D",
            "quantity": 1
        }],
        success_url=BASE_URL,
        cancel_url=BASE_URL
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

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        c.execute("""
            UPDATE users
            SET customer_id = ?, subscription_status = 'active'
            WHERE email = ?
        """, (session.customer, session.customer_email))

        conn.commit()
        conn.close()

    return "OK", 200

# =========================
# APP (POLISHED UI)
# =========================

@app.route("/app")
def app_screen():
    return f"""
    <html>
    <body style="margin:0;font-family:Arial;background:#0b1b3a;color:white;">

    <!-- EULA MODAL -->
    <div id="eulaModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);">

        <div style="background:#12275a;width:60%;margin:80px auto;padding:25px;border-radius:10px;">
            <h2>Terms, Privacy & AI Notice</h2>

            <div style="height:200px;overflow:auto;background:#0b1b3a;padding:10px;border-radius:6px;">
                <p><b>Service:</b> HiddenEdge provides AI-based career insights.</p>
                <p><b>AI:</b> Outputs are advisory and not guaranteed.</p>
                <p><b>Data:</b> CV is processed temporarily. Email stored for access.</p>
                <p><b>Payments:</b> Non-refundable.</p>
                <p><b>Contact:</b> HiddenEdgeInfo@proton.me</p>
            </div>

            <br>
            <input type="checkbox" id="agree"> I accept
            <br><br>
            <button onclick="acceptEula()" style="padding:10px 20px;background:#4ea3ff;border:none;border-radius:6px;color:white;">
                Continue
            </button>
        </div>
    </div>

    <!-- MAIN -->
    <div style="max-width:900px;margin:40px auto;padding:20px;">

        <h1 style="text-align:center;">🚀 HiddenEdge</h1>

        <div style="margin-top:30px;background:#12275a;padding:20px;border-radius:10px;">
            <h3>Upload CV</h3>
            <input type="file" id="cvFile">
        </div>

        <div style="margin-top:20px;background:#12275a;padding:20px;border-radius:10px;">
            <h3>Job Description</h3>
            <textarea id="job" rows="8" style="width:100%;border-radius:6px;"></textarea>
        </div>

        <div style="text-align:center;margin-top:20px;">
            <button onclick="analyze()"
                    style="padding:12px 30px;background:#4ea3ff;border:none;border-radius:6px;color:white;font-size:16px;">
                Analyze
            </button>
        </div>

        <div style="margin-top:30px;background:#1b3a6b;padding:20px;border-radius:10px;">
            <h3>Nestor AI</h3>
            <pre id="result"></pre>
        </div>

    </div>

    <!-- FOOTER -->
    <div style="text-align:center;margin-top:40px;font-size:12px;color:#aaa;padding:20px;">
        HiddenEdgeInfo@proton.me | SB3PM Advisory and Services Ltd, HiddenEdge is part of ProductiveYou services branch
    </div>

    <script>

    const email = localStorage.getItem("he_email");

    if (!email) {{
        window.location.href = "/";
    }}

    async function checkEula() {{
        const res = await fetch("/check_eula", {{
            method:"POST",
            headers:{{"Content-Type":"application/json"}},
            body:JSON.stringify({{email}})
        }});
        const data = await res.json();
        if (!data.accepted) {{
            document.getElementById("eulaModal").style.display = "block";
        }}
    }}

    async function acceptEula() {{
        if (!document.getElementById("agree").checked) {{
            alert("You must accept");
            return;
        }}

        await fetch("/accept_eula", {{
            method:"POST",
            headers:{{"Content-Type":"application/json"}},
            body:JSON.stringify({{email}})
        }});

        document.getElementById("eulaModal").style.display = "none";
    }}

    let cvText = "";

    document.getElementById("cvFile").addEventListener("change", function() {{
        const reader = new FileReader();
        reader.onload = e => cvText = e.target.result;
        reader.readAsText(this.files[0]);
    }});

    async function analyze() {{
        const res = await fetch("/analyze", {{
            method:"POST",
            headers:{{"Content-Type":"application/json"}},
            body:JSON.stringify({{
                email,
                cv:cvText,
                job:document.getElementById("job").value
            }})
        }});

        const data = await res.json();

        if (data.blocked) {{
            alert("Free limit reached. Redirecting to payment.");
            const checkout = await fetch("/create_checkout", {{
                method:"POST",
                headers:{{"Content-Type":"application/json"}},
                body:JSON.stringify({{email}})
            }});
            const cdata = await checkout.json();
            window.location.href = cdata.url;
            return;
        }}

        document.getElementById("result").innerText =
            data.nestor.decision + "\\n" + data.nestor.reason;
    }}

    checkEula();

    </script>

    </body>
    </html>
    """

# =========================
# ANALYZE
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    email = data.get("email")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT usage_count, subscription_status FROM users WHERE email = ?", (email,))
    row = c.fetchone()

    if not row:
        c.execute("INSERT INTO users (email) VALUES (?)", (email,))
        usage = 0
        paid = False
    else:
        usage, sub = row
        paid = sub == "active"

    if not paid and usage >= FREE_LIMIT:
        conn.close()
        return jsonify({"blocked": True})

    if not paid:
        c.execute("UPDATE users SET usage_count = usage_count + 1 WHERE email = ?", (email,))
        conn.commit()

    conn.close()

    return jsonify({
        "blocked": False,
        "nestor": {"decision": "OK", "reason": "Analysis complete"}
    })

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(port=5000, debug=True)