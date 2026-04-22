print("=== NEW BACKEND VERSION LOADED ===")

from flask import Flask, request, jsonify, render_template, redirect
import os
import stripe
import docx
import json
from openai import OpenAI

app = Flask(__name__)

# =========================
# CONFIG
# =========================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

stripe.api_key = STRIPE_SECRET_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# HELPERS
# =========================

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return ""

def clean_json_response(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()
    return raw

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/app")
def app_page():
    return render_template("app.html", stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route("/eula")
def eula():
    return render_template("eula.html")

@app.route("/email")
def email():
    return render_template("email.html")

@app.route("/success")
def success():
    return render_template("success.html")

# =========================
# ANALYZE (AI ENGINE)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        cv_file = request.files.get("cv_file")
        job_description = request.form.get("job_description", "")

        if not cv_file:
            return jsonify({"error": "No CV uploaded"})

        # Extract CV
        if cv_file.filename.endswith(".docx"):
            cv_text = extract_text_from_docx(cv_file)
        else:
            cv_text = cv_file.read().decode("utf-8", errors="ignore")

        if not cv_text.strip():
            return jsonify({
                "fit_score": 0,
                "decision": "Error",
                "recruiter_view": "CV unreadable",
                "hiring_manager_view": "Invalid CV format",
                "recommended_roles": []
            })

        prompt = f"""
You are two professionals evaluating a candidate:

1. Recruiter → screening, positioning, CV fit
2. Hiring Manager → delivery capability, risk, impact

Return ONLY valid JSON:

{{
"fit_score": number,
"decision": "Strong Apply | Consider | Reject",
"recruiter_view": "...",
"hiring_manager_view": "...",
"recommended_roles": ["...", "..."]
}}

Rules:
- recruiter_view and hiring_manager_view must be different
- recommended_roles MUST ALWAYS contain 3–5 roles
- roles must be realistic based on CV + job
- no markdown
- no explanation outside JSON

CV:
{cv_text[:4000]}

JOB:
{job_description[:4000]}
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw = response.choices[0].message.content
        raw = clean_json_response(raw)

        try:
            parsed = json.loads(raw)
        except:
            return jsonify({
                "fit_score": 0,
                "decision": "Error",
                "recruiter_view": raw,
                "hiring_manager_view": "Parsing failed",
                "recommended_roles": []
            })

        return jsonify({
            "fit_score": parsed.get("fit_score", 0),
            "decision": parsed.get("decision", "Error"),
            "recruiter_view": parsed.get("recruiter_view", ""),
            "hiring_manager_view": parsed.get("hiring_manager_view", ""),
            "recommended_roles": parsed.get("recommended_roles", [])
        })

    except Exception as e:
        return jsonify({
            "fit_score": 0,
            "decision": "Error",
            "recruiter_view": "System error",
            "hiring_manager_view": str(e),
            "recommended_roles": []
        })

# =========================
# STRIPE
# =========================

@app.route("/create-checkout-session")
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "HiddenEdge Premium Access"
                    },
                    "unit_amount": 900,
                },
                "quantity": 1,
            }],
            success_url=request.host_url + "success",
            cancel_url=request.host_url + "app"
        )

        return redirect(session.url)

    except Exception as e:
        return str(e)

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)