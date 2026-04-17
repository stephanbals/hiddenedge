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

# ================= UI =================
@app.route("/")
def home():
    return """
    <html><body style="background:#0b1b3a;color:white;text-align:center;padding:50px;">
    <h1>HiddenEdge</h1>

    <input id="email"><br><br>
    <button onclick="go()">Start</button>

    <script>
    function go(){
        localStorage.setItem("email",document.getElementById("email").value);
        window.location="/app";
    }
    </script>
    </body></html>
    """

@app.route("/app")
def app_ui():
    return """
    <html><body style="background:#0b1b3a;color:white;padding:40px;">

    <input type="file" id="cv" accept=".docx,.pdf,.txt"><br><br>
    <textarea id="job" rows="6" style="width:100%;"></textarea><br><br>

    <button onclick="run()">Analyze</button>

    <div id="barBox" style="display:none;margin-top:20px;">
        <div style="background:#222;height:20px;">
            <div id="bar" style="height:100%;width:0%;background:#4ea3ff;"></div>
        </div>
    </div>

    <pre id="out"></pre>

    <script>

    let f;

    document.getElementById("cv").onchange=e=>f=e.target.files[0];

    function animate(){
        let w=0;
        let b=document.getElementById("bar");
        let i=setInterval(()=>{
            w+=10;
            b.style.width=w+"%";
            if(w>=100) clearInterval(i);
        },200);
    }

    async function run(){

        document.getElementById("barBox").style.display="block";
        animate();

        const fd=new FormData();
        fd.append("email",localStorage.getItem("email"));
        fd.append("job",document.getElementById("job").value);
        fd.append("files",f);

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

        document.getElementById("out").innerText=
            JSON.stringify(d,null,2);
    }

    </script>

    </body></html>
    """

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)