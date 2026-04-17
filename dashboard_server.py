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

# ================= LANDING PAGE =================
@app.route("/")
def home():
    return """
    <html>
    <body style="margin:0;background:#0b1b3a;color:white;font-family:Arial;">

    <div style="text-align:center;padding:80px;">

        <h1 style="font-size:48px;margin-bottom:20px;">HiddenEdge</h1>

        <div style="font-size:80px;">🤖</div>

        <h2 style="margin-top:20px;">Stop applying to the wrong jobs.</h2>

        <p style="max-width:700px;margin:auto;font-size:18px;">
        HiddenEdge tells you if applying is worth it — and then helps you stand out when it is.
        </p>

        <br><br>

        <button onclick="start()" 
        style="padding:20px 50px;font-size:24px;background:#4ea3ff;color:white;border:none;border-radius:12px;">
            🚀 START HERE
        </button>

        <br><br><br>

        <div style="display:flex;justify-content:center;gap:40px;flex-wrap:wrap;">

            <div style="background:#1c2e5a;padding:25px;border-radius:12px;width:300px;">
                <div style="font-size:40px;">👔🤖</div>
                <h3>Nestor analyzes</h3>
                <p>Should you apply?</p>
                <ul style="text-align:left;">
                    <li>Strong match</li>
                    <li>Stretch</li>
                    <li>Do not apply</li>
                </ul>
            </div>

            <div style="background:#1c2e5a;padding:25px;border-radius:12px;width:300px;">
                <div style="font-size:40px;">💻🤖</div>
                <h3>Alec refines</h3>
                <p>Strengthens your CV</p>
                <ul style="text-align:left;">
                    <li>Tailored CV</li>
                    <li>Better positioning</li>
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

# ================= TOOL PAGE =================
@app.route("/app")
def app_ui():
    return """
    <html>
    <body style="background:#0b1b3a;color:white;font-family:Arial;padding:40px;">

    <h2>HiddenEdge</h2>

    <div style="font-size:60px;">🤖</div>
    <p>Welcome — let’s make smarter application decisions.</p>

    <input type="file" id="cv"><br><br>
    <textarea id="job" rows="6" style="width:100%;"></textarea><br><br>

    <button onclick="run()">Analyze</button>

    <div id="nestor" style="margin-top:40px;"></div>
    <div id="alec" style="margin-top:40px;"></div>
    <div id="download" style="margin-top:40px;"></div>
    <div id="continue" style="margin-top:40px;"></div>

    <script>

    let file;
    let currentCV = "";

    document.getElementById("cv").onchange=e=>file=e.target.files[0];

    function showThinking(){
        document.getElementById("nestor").innerHTML = "<p>👔🤖 Nestor is thinking...</p>";
    }

    function renderNestor(data){
        const n = data.nestor;
        const strengths = n.strengths ? n.strengths.join(", ") : "N/A";
        const gaps = n.gaps ? n.gaps.join(", ") : "N/A";

        document.getElementById("nestor").innerHTML = `
            <h3>Nestor Decision</h3>
            <p><b>${n.decision}</b> (${n.fit_score}/10)</p>
            <p><b>Strengths:</b> ${strengths}</p>
            <p><b>Gaps:</b> ${gaps}</p>
        `;
    }

    function renderAlec(data){
        currentCV = data.alec.cv;

        document.getElementById("alec").innerHTML = `
            <h3>Alec</h3>
            <p>Rewriting your CV...</p>
            <pre>${currentCV}</pre>
        `;
    }

    function renderDownload(){
        document.getElementById("download").innerHTML = `
            <button onclick="download()">Download CV</button>
        `;
    }

    function renderContinue(){
        document.getElementById("continue").innerHTML = `
            <p>Analyze another job?</p>
            <button onclick="location.reload()">Yes</button>
            <button onclick="exit()">No</button>
        `;
    }

    function exit(){
        alert("Thank you — come back soon!");
        window.location = "https://google.com";
    }

    async function download(){
        const res = await fetch("/download_cv",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({cv: currentCV})
        });

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "HiddenEdge_CV.docx";
        a.click();
    }

    async function run(){

        if(!file){
            alert("Upload CV first");
            return;
        }

        showThinking();

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

        renderNestor(d);
        renderAlec(d);
        renderDownload();
        renderContinue();
    }

    </script>

    </body>
    </html>
    """

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)