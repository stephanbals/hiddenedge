from flask import Flask, request, jsonify, send_file
import stripe
import os
import sqlite3
from io import BytesIO

from core.cv.cv_service import extract_text_from_files, evaluate_fit, tailor_cv
from core.cv.doc_export import generate_docx

app = Flask(__name__)

# ================= CONFIG =================
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BASE_URL = os.getenv("BASE_URL")

DB_FILE = "app.db"
FREE_LIMIT = 3

# ================= DB =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            usage_count INTEGER DEFAULT 0,
            subscription_status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= STRIPE =================
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
        success_url=BASE_URL + "/app",
        cancel_url=BASE_URL + "/app"
    )

    return jsonify({"url": session.url})

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except:
        return "fail", 400

    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        email = s.get("customer_email")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO users(email, usage_count, subscription_status)
            VALUES(?, 0, 'active')
        """, (email,))
        conn.commit()
        conn.close()

    return "ok", 200

# ================= ANALYZE =================
@app.route("/analyze", methods=["POST"])
def analyze():
    email = request.form.get("email")
    job = request.form.get("job")
    files = request.files.getlist("files")

    if not files or files[0].filename == "":
        return jsonify({"error": "No CV uploaded"})

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT usage_count, subscription_status FROM users WHERE email=?", (email,))
    row = c.fetchone()

    if not row:
        c.execute("INSERT INTO users(email) VALUES(?)", (email,))
        usage = 0
        paid = False
    else:
        usage, sub = row
        paid = sub == "active"

    if not paid and usage >= FREE_LIMIT:
        conn.close()
        return jsonify({"blocked": True})

    if not paid:
        c.execute("UPDATE users SET usage_count = usage_count + 1 WHERE email=?", (email,))
        conn.commit()

    conn.close()

    texts = extract_text_from_files(files)

    if not texts or texts[0].strip() == "":
        return jsonify({"error": "CV could not be read"})

    evaluation = evaluate_fit(texts, job)
    cv = tailor_cv(texts, job, evaluation)

    return jsonify({
        "blocked": False,
        "nestor": evaluation,
        "alec": {"cv": cv}
    })

# ================= DOWNLOAD =================
@app.route("/download_cv", methods=["POST"])
def download_cv():
    cv = request.json.get("cv")
    file_bytes = generate_docx(cv)

    return send_file(
        BytesIO(file_bytes),
        as_attachment=True,
        download_name="HiddenEdge_CV.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# ================= LANDING (PIXEL UI) =================
@app.route("/")
def home():
    return """
    <html>
    <head>
    <style>
        body {
            margin:0;
            font-family:Arial;
            background: radial-gradient(circle at top, #1a0f3c, #050010);
            color:white;
        }

        .container {
            text-align:center;
            padding:60px 20px;
        }

        .hero {
            padding:40px;
            border-radius:20px;
            background: rgba(255,255,255,0.05);
            box-shadow: 0 0 40px rgba(80,120,255,0.3);
            max-width:900px;
            margin:auto;
        }

        .glow {
            text-shadow: 0 0 10px #4ea3ff, 0 0 20px #4ea3ff;
        }

        .start-btn {
            margin-top:20px;
            padding:18px 40px;
            font-size:22px;
            background:#4ea3ff;
            border:none;
            border-radius:12px;
            color:white;
            cursor:pointer;
            box-shadow:0 0 20px #4ea3ff;
        }

        .cards {
            display:flex;
            justify-content:center;
            gap:30px;
            margin-top:50px;
            flex-wrap:wrap;
        }

        .card {
            width:380px;
            padding:25px;
            border-radius:15px;
            background: rgba(255,255,255,0.05);
            box-shadow:0 0 30px rgba(0,0,0,0.6);
        }
    </style>
    </head>

    <body>

    <div class="container">

        <h1 class="glow">HiddenEdge</h1>

        <div class="hero">
            <div style="font-size:80px;">🤖</div>

            <h2 class="glow">Welcome to HiddenEdge</h2>
            <p>Let’s make your CV get noticed.</p>

            <button class="start-btn" onclick="start()">
                🚀 START HERE
            </button>

            <p style="font-size:12px;color:#aaa;">
                HiddenEdge determines your success probability and upgrades your CV
            </p>
        </div>

        <div class="cards">

            <div class="card">
                <div style="font-size:50px;">👔🤖</div>
                <h3>NESTOR ANALYZES</h3>
                <h2>Should you apply?</h2>
                <ul style="text-align:left;">
                    <li>Strong Match</li>
                    <li>Stretch Opportunity</li>
                    <li>Rethink</li>
                </ul>
            </div>

            <div class="card">
                <div style="font-size:50px;">💻🤖</div>
                <h3>ALEC REFINES</h3>
                <h2>Fit the role perfectly</h2>
                <ul style="text-align:left;">
                    <li>Tailored CV</li>
                    <li>Upgrade your CV</li>
                </ul>
            </div>

        </div>

    </div>

    <script>
    function start(){
        const email = prompt("Enter your email:");
        if(email){
            localStorage.setItem("email", email);
            window.location = "/app";
        }
    }
    </script>

    </body>
    </html>
    """

# ================= TOOL =================
@app.route("/app")
def app_ui():
    return """
    <html>
    <body style="background:#0b1b3a;color:white;font-family:Arial;padding:40px;">

    <h2>HiddenEdge Tool</h2>

    <input type="file" id="cv"><br><br>
    <textarea id="job" rows="6" style="width:100%;"></textarea><br><br>

    <button onclick="run()">Analyze</button>

    <div id="nestor"></div>
    <div id="alec"></div>
    <div id="download"></div>

    <script>
    let file;
    let currentCV = "";

    document.getElementById("cv").onchange=e=>file=e.target.files[0];

    async function run(){
        if(!file){ alert("Upload CV first"); return; }

        const fd=new FormData();
        fd.append("email",localStorage.getItem("email"));
        fd.append("job",document.getElementById("job").value);
        fd.append("files",file);

        const r=await fetch("/analyze",{method:"POST",body:fd});
        const d=await r.json();

        if(d.blocked){
            const pay=await fetch("/create_checkout",{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body:JSON.stringify({email:localStorage.getItem("email")})
            });
            const p=await pay.json();
            window.location=p.url;
            return;
        }

        currentCV = d.alec.cv;
        document.getElementById("alec").innerText = currentCV;
    }
    </script>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)