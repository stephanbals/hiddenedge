from flask import Flask, render_template, request, jsonify
import os
import stripe
from openai import OpenAI
import json
import re
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

        # HARD PAYWALL
        if not user["paid"] and user["attempts"] >= 3:
            return jsonify({"error": "PAYWALL"}), 403

        job_text = request.form.get("job_text", "")
        file = request.files.get("file")

        cv_text = extract_cv(file)

        prompt = f"""
You are Nestor, a strict hiring evaluator.

You MUST:
- Speak directly to the candidate ("you")
- NEVER give advice to employers
- Be direct, realistic, and actionable

SCORING RULES:
- Missing mandatory qualifications → score MUST be below 20
- Domain mismatch → strong penalty
- Overqualification must NOT reduce score

ALTERNATIVE ROLE RULE:
- If score < 50 → ALWAYS provide 3 realistic alternative roles

Return ONLY JSON:

{{
  "fit_score": number,
  "recruiter_view": "...",
  "hiring_manager_view": "...",
  "gaps": ["...", "...", "..."],
  "actions": ["...", "...", "..."],
  "alternative_roles": ["...", "...", "..."]
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
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}

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
        return jsonify({"error": str(e)}), 500

# ================= ALEC =================

@app.route("/alec", methods=["POST"])
def alec():
    email = request.form.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Missing email"}), 400

    user = get_user(email)

    if not user["paid"] and user["attempts"] >= 3:
        return jsonify({"error": "PAYWALL"}), 403

    file = request.files.get("file")
    job_text = request.form.get("job_text", "")

    cv_text = extract_cv(file)

    prompt = f"""
You are Alec, a senior CV optimization expert.

Rewrite the CV to better match the job.

Rules:
- Do NOT invent experience
- Improve clarity and structure
- Align with job keywords
- Keep it professional

Return ONLY the CV text.

CV:
{cv_text[:3000]}

JOB:
{job_text[:2000]}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return jsonify({
        "cv": response.choices[0].message.content.strip()
    })

# ================= DOWNLOAD =================

@app.route("/download_cv", methods=["POST"])
def download_cv():
    data = request.json or {}
    cv_text = data.get("cv", "")

    from docx import Document
    doc = Document()

    for line in cv_text.split("\n"):
        doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer.getvalue(), 200, {
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Content-Disposition": "attachment; filename=HiddenEdge_CV.docx"
    }

# ================= STRIPE =================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= UNLOCK =================

@app.route("/unlock", methods=["POST"])
def unlock():
    data = request.json
    email = data.get("email")

    user = get_user(email)
    user["paid"] = True
    update_user(email, user)

    return jsonify({"status": "ok"})

# ================= NO CACHE =================

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)