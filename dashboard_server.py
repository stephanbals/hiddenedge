import os
import stripe
import sqlite3
import logging
from flask import Flask, request, jsonify, render_template
import io
from docx import Document
import PyPDF2

# ---------------- CONFIG ----------------

app = Flask(__name__, template_folder="templates")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL")

stripe.api_key = STRIPE_SECRET_KEY

FREE_LIMIT = 3
DB_FILE = "users.db"
LOG_FILE = "app.log"

# ---------------- LOGGING SETUP ----------------

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
        logger.info(f"NEW USER CREATED: {email}")
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
            logger.warning("ANALYZE FAILED: missing email")
            return jsonify({"error": "Missing email"}), 400

        user = get_user(email)

        logger.info(f"ANALYZE REQUEST: {email} | usage={user['usage']} | paid={user['paid']}")

        # PAYWALL
        if not user["paid"] and user["usage"] >= FREE_LIMIT:
            logger.info(f"PAYWALL HIT: {email}")
            return jsonify({"paywall": True}), 403

        file = request.files.get("cv_file")
        job = request.form.get("job_description")

        if not file or not job:
            logger.warning(f"ANALYZE FAILED INPUT: {email}")
            return jsonify({"error": "Missing input"}), 400

        file_bytes = file.read()
        cv_text = extract_text(file.filename, file_bytes)

        score = min(95, 50 + len(cv_text) % 50)

        result = {
            "score": score,
            "decision": "Strong Match" if score > 75 else "Moderate Match",
            "strengths": ["Relevant experience", "Clear structure"],
            "gaps": ["Missing metrics", "Weak keyword alignment"],
            "improvements": [
                "Add measurable results",
                "Tailor summary",
                "Align keywords"
            ]
        }

        # TRACK USAGE
        if not user["paid"]:
            new_usage = user["usage"] + 1
            update_user(email, usage=new_usage)
            result["remaining"] = FREE_LIMIT - new_usage
            logger.info(f"USAGE UPDATED: {email} → {new_usage}")
        else:
            result["remaining"] = "∞"

        result["paid"] = bool(user["paid"])

        return jsonify(result)

    except Exception as e:
        logger.exception("ANALYZE CRASH")
        return jsonify({"error": "Analyze failed"}), 500

# ---------------- STRIPE CHECKOUT ----------------

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    try:
        data = request.json or {}
        email = data.get("email")

        logger.info(f"CHECKOUT START: {email}")

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

    except Exception as e:
        logger.exception("STRIPE CHECKOUT ERROR")
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
    except Exception as e:
        logger.exception("WEBHOOK SIGNATURE ERROR")
        return "", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")

        if email:
            update_user(email, paid=1)
            logger.info(f"PAYMENT SUCCESS → USER UNLOCKED: {email}")

    return "", 200

# ---------------- RUN ----------------

if __name__ == "__main__":
    logger.info("🚀 Starting HiddenEdge server...")
    app.run(host="0.0.0.0", port=5000)