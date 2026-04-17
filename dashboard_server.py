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

# ================= HOME =================
@app.route("/")
def home():
    return """
    <html>
    <body style="background:#0b1b3a;color:white;text-align:center;padding:50px;font-family:Arial;">
        <h1>HiddenEdge</h1>

        <input id="email" placeholder="Enter email"><br><br>
        <button onclick="go()">Start</button>

        <script>
        function go(){
            localStorage.setItem("email",document.getElementById("email").value);
            window.location="/app";
        }
        </script>
    </body>
    </html>
    """

# ================= APP UI =================
@app.route("/app")
def app_ui():
    return """
    <html>
    <body style="background:#0b1b3a;color:white;font-family:Arial;">

    <!-- HEADER -->
    <div style="display:flex;justify-content:space-between;padding:20px;">
        <h2>HiddenEdge</h2>
        <button onclick="toggleHelp()" style="padding:10px;background:#4ea3ff;border:none;color:white;border-radius:6px;">
            Help
        </button>
    </div>

    <!-- HELP MODAL -->
    <div id="helpBox" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;
        background:rgba(0,0,0,0.9);padding:40px;overflow:auto;">

        <h2>How to use HiddenEdge</h2>

        <ol>
            <li>Upload your CV (.docx, .pdf, .txt)</li>
            <li>Paste job description</li>
            <li>Click Analyze</li>
            <li>Nestor evaluates your fit</li>
            <li>Alec rewrites your CV</li>
            <li>Download improved CV</li>
        </ol>

        <p>Free: 3 analyses → then payment required.</p>

        <button onclick="toggleHelp()">Close</button>
    </div>

    <!-- MAIN -->
    <div style="max-width:900px;margin:auto;padding:30px;">

        <h3>Upload CV</h3>
        <input type="file" id="cv" accept=".docx,.pdf,.txt"><br><br>

        <h3>Job Description</h3>
        <textarea id="job" rows="6" style="width:100%;"></textarea><br><br>

        <button onclick="run()" style="padding:12px 20px;background:#4ea3ff;border:none;color:white;border-radius:6px;">
            Analyze
        </button>

        <!-- PROGRESS -->
        <div id="barBox" style="display:none;margin-top:20px;">
            <div style="background:#222;height:20px;">
                <div id="bar" style="height:100%;width:0%;background:#4ea3ff;"></div>
            </div>
        </div>

        <!-- OUTPUT -->
        <pre id="out" style="margin-top:20px;"></pre>

    </div>

    <script>

    let file;

    document.getElementById("cv").onchange=e=>{
        file=e.target.files[0];
    };

    function toggleHelp(){
        const h=document.getElementById("helpBox");
        h.style.display = (h.style.display === "none") ? "block" : "none";
    }

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

        if(!file){
            alert("Upload CV first");
            return;
        }

        document.getElementById("barBox").style.display="block";
        animate();

        const fd=new FormData();
        fd.append("email",localStorage.getItem("email"));
        fd.append("job",document.getElementById("job").value);
        fd.append("files",file);

        const r=await fetch("/analyze",{method:"POST",body:fd});
        const d=await r.json();

        if(d.error){
            alert(d.error);
            return;
        }

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

        document.getElementById("out").innerText =
            JSON.stringify(d,null,2);
    }

    </script>

    </body>
    </html>
    """

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)