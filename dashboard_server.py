import os
import stripe
import pdfplumber
from docx import Document
from flask import Flask, request, jsonify, render_template

# ------------------------
# CONFIG
# ------------------------

app = Flask(__name__, template_folder="templates")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL")

if not STRIPE_SECRET_KEY:
    raise ValueError("Missing STRIPE_SECRET_KEY")

if not STRIPE_PRICE_ID:
    raise ValueError("Missing STRIPE_PRICE_ID")

stripe.api_key = STRIPE_SECRET_KEY

# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/app")
def app_page():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ------------------------
# FILE PARSING
# ------------------------

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text(file):
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file)

    elif filename.endswith(".docx"):
        return extract_text_from_docx(file)

    elif filename.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")

    else:
        return ""

# ------------------------
# ANALYZE
# ------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "cv_file" not in request.files:
            return jsonify({"error": "No CV uploaded"}), 400

        file = request.files["cv_file"]
        job_description = request.form.get("job_description")

        if file.filename == "":
            return jsonify({"error": "Empty file"}), 400

        if not job_description:
            return jsonify({"error": "Missing job description"}), 400

        cv_text = extract_text(file)

        if not cv_text.strip():
            return jsonify({"error": "Could not extract text from CV"}), 400

        # ------------------------
        # TEMP LOGIC (replace later)
        # ------------------------
        score = 85
        decision = "Strong Match"

        return jsonify({
            "score": score,
            "decision": decision
        })

    except Exception as e:
        print("❌ Analyze error:", str(e))
        return jsonify({"error": "Analyze failed"}), 500

# ------------------------
# STRIPE
# ------------------------

@app.route("/create_checkout", methods=["POST"])
def create_checkout():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{BASE_URL}/app?success=true",
            cancel_url=f"{BASE_URL}/app?canceled=true",
        )

        return jsonify({"url": session.url})

    except Exception as e:
        print("❌ Stripe error:", str(e))
        return jsonify({"error": "Checkout failed"}), 500

# ------------------------
# WEBHOOK
# ------------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print("❌ Webhook error:", str(e))
        return "", 400

    if event["type"] == "checkout.session.completed":
        print("✅ Payment completed")

    return "", 200

# ------------------------
# RUN
# ------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)