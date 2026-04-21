from flask import Flask, render_template, request, jsonify
import os
import stripe
from openai import OpenAI
import json
from io import BytesIO

app = Flask(__name__, static_folder="static", template_folder="templates")

# ===== INIT =====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

USERS_FILE = "users.json"

# ===== STORAGE =====

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def get_user(email):
    users = load_users()
    if email not in users:
        users[email] = {"attempts": 0, "paid": False}
        save_users(users)
    return users[email]

def update_user(email, data):
    users = load_users()
    users[email] = data
    save_users(users)

# ================= ROUTES =================

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/eula")
def eula():
    return render_template("eula.html")

@app.route("/email")
def email():
    return render_template("email.html")

@app.route("/app")
def app_page():
    return render_template("app.html")

@app.route("/success")
def success():
    return render_template("success.html")

# ================= HELPERS =================

def map_decision(score):
    if score < 20:
        return "Reject"
    elif score < 50:
        return "Weak Match"
    elif score < 70:
        return "Moderate Match"
    elif score < 85:
        return "Strong Match"
    else:
        return "Excellent Fit"

def extract_cv(file):
    if not file:
        return ""

    filename = file.filename.lower()

    if filename.endswith(".docx"):
        from docx import Document
        doc = Document(BytesIO(file.read()))
        return "\n".join([p.text for p in doc.paragraphs])

    elif filename.endswith(".pdf"):
        import PyPDF2
        reader = PyPDF2.PdfReader(BytesIO(file.read()))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except:
                pages.append("")
        return "\n".join(pages)

    else:
        return file.read().decode("utf-8", errors="ignore")

# ================= ANALYZE =================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        email = request.form.get("email", "").strip().lower()
        if not email:
            return jsonify({"error": "Missing email"}), 400

        user = get_user(email)

        if not user["paid"] and user["attempts"] >= 3:
            return jsonify({"error": "PAYWALL"}), 403

        job_text = request.form.get("job_text", "")
        file = request.files.get("file")
        cv_text = extract_cv(file)

        prompt = f"""
You are Nestor, a strict hiring evaluator.

Return ONLY VALID JSON. No text. No explanation.

Format:
{{
  "fit_score": number,
  "recruiter_view": "string",
  "hiring_manager_view": "string",
  "gaps": ["string"],
  "actions": ["string"],
  "alternative_roles": ["string"]
}}

CV:
{cv_text[:3000]}

JOB:
{job_text[:2000]}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw = response.choices[0].message.content.strip()

        # 🔥 DIRECT JSON PARSE (NO REGEX)
        try:
            data = json.loads(raw)
        except:
            print("RAW BAD JSON:", raw)
            data = {}

        score = int(data.get("fit_score", 0))
        decision = map_decision(score)

        if not user["paid"]:
            user["attempts"] += 1
            update_user(email, user)

        return jsonify({
            "nestor": {
                "decision": decision,
                "fit_score": score,
                "recruiter_view": data.get("recruiter_view", ""),
                "hiring_manager_view": data.get("hiring_manager_view", "")
            },
            "gaps": data.get("gaps", []),
            "actions": data.get("actions", []),
            "alternative_roles": data.get("alternative_roles", [])
        })

    except Exception as e:
        print("ANALYZE ERROR:", str(e))
        return jsonify({
            "nestor": {
                "decision": "Error",
                "fit_score": 0,
                "recruiter_view": "System error",
                "hiring_manager_view": str(e)
            },
            "gaps": [],
            "actions": [],
            "alternative_roles": []
        }), 200

# ================= STRIPE =================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    email = data.get("email")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        customer_email=email,
        line_items=[{
            "price": STRIPE_PRICE_ID,
            "quantity": 1,
        }],
        success_url=f"{BASE_URL}/success",
        cancel_url=f"{BASE_URL}/app",
    )

    return jsonify({"url": session.url})

# ================= UNLOCK =================

@app.route("/unlock", methods=["POST"])
def unlock():
    data = request.json
    email = data.get("email")

    user = get_user(email)
    user["paid"] = True
    update_user(email, user)

    return jsonify({"status": "ok"})

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)