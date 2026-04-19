import os
import stripe
import sqlite3
import logging
import io
import json

from flask import Flask, request, jsonify, render_template
from docx import Document
import PyPDF2
from openai import OpenAI

# ---------------- CONFIG ----------------

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not STRIPE_SECRET_KEY:
    raise ValueError("Missing STRIPE_SECRET_KEY")

if not STRIPE_WEBHOOK_SECRET:
    raise ValueError("Missing STRIPE_WEBHOOK_SECRET")

if not STRIPE_PRICE_ID:
    raise ValueError("Missing STRIPE_PRICE_ID")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

stripe.api_key = STRIPE_SECRET_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

FREE_LIMIT = 3
DB_FILE = "users.db"
LOG_FILE = "app.log"

# ---------------- LOGGING ----------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            usage INTEGER DEFAULT 0,
            paid INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

def get_user(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT usage, paid FROM users WHERE email=?", (email,))
    row = c.fetchone()

    if not row:
        c.execute("INSERT INTO users (email, usage, paid) VALUES (?, 0, 0)", (email,))
        conn.commit()
        conn.close()
        logger.info(f"NEW USER: {email}")
        return {"usage": 0, "paid": 0}

    conn.close()
    return {"usage": row[0], "paid": row[1]}

def update_user(email, usage=None, paid=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if usage is not None:
        c.execute("UPDATE users SET usage=? WHERE email=?", (usage, email))

    if paid is not None:
        c.execute("UPDATE users SET paid=? WHERE email=?", (paid, email))

    conn.commit()
    conn.close()

init_db()

# ---------------- FILE PARSING ----------------

def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text(filename, file_bytes):
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    if filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    return file_bytes.decode("utf-8", errors="ignore")

# ---------------- AI ANALYSIS ----------------

def analyze_with_ai(cv_text, job_text):
    prompt = f"""
You are a senior recruiter.

Evaluate how well this CV matches the job.

Return ONLY valid JSON.

Format:
{{
  "score": number (0-100),
  "decision": "Strong Match" | "Moderate Match" | "Weak Match",
  "strengths": ["specific strengths tied to job"],
  "gaps": ["specific missing elements vs job"],
  "improvements": ["actionable improvements"],
  "advice": "should the candidate apply or not and why"
}}

Rules:
- Be specific
- Avoid generic statements
- Max 5 items per list

CV:
{cv_text}

JOB:
{job_text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw = response.choices[0].message.content.strip()
        return json.loads(raw)

    except Exception:
        logger.exception("AI ERROR")
        return {
            "score": 50,
            "decision": "Moderate Match",
            "strengths": ["AI failed"],
            "gaps": ["AI failed"],
            "improvements": ["Retry"],
            "advice": "Unable to determine"
        }

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/app")
def app_page():
    return render_template("index.html")

# ---------------- ANALYZE ----------------

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        email = request.form.get("email")

        if not email:
            return jsonify({"error": "Missing email"}), 400

        user = get_user(email)

        if not user["paid"] and user["usage"] >= FREE_LIMIT:
            return jsonify({"paywall": True}), 403

        file = request.files.get("cv_file")
        job = request.form.get("job_description")

        if not file or not job:
            return jsonify({"error": "Missing input"}), 400

        file_bytes = file.read()
        cv_text = extract_text(file.filename, file_bytes)

        result = analyze_with_ai(cv_text, job)

        if not user["paid"]:
            new_usage = user["usage"] + 1
            update_user(email, usage=new_usage)
            result["remaining"] = FREE_LIMIT - new_usage
        else:
            result["remaining"] = "∞"

        result["paid"] = bool(user["paid"])

        return jsonify(result)

    except Exception:
        logger.exception("ANALYZE ERROR")
        return jsonify({"error": "Analyze failed"}), 500

# ---------------- STRIPE ----------------

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    try:
        data = request.json or {}
        email = data.get("email")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{BASE_URL}/app?success=true",
            cancel_url=f"{BASE_URL}/app",
        )

        return jsonify({"url": session.url})

    except Exception:
        logger.exception("STRIPE ERROR")
        return jsonify({"error": "Checkout failed"}), 500

# ---------------- WEBHOOK ----------------

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        logger.exception("WEBHOOK ERROR")
        return "", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")

        if email:
            update_user(email, paid=1)
            logger.info(f"USER UNLOCKED: {email}")

    return "", 200

# ---------------- RUN ----------------

if __name__ == "__main__":
    logger.info("Starting HiddenEdge...")
    app.run(host="0.0.0.0", port=5000)