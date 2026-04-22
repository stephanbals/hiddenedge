print("=== NEW BACKEND VERSION LOADED ===")

from flask import Flask, request, jsonify, render_template
import os
import stripe
import re
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

FREE_LIMIT = 3
usage_counter = {}

# =========================
# UTIL
# =========================
def normalize(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())

def extract_tokens(text):
    return set(normalize(text).split())

# =========================
# ROUTES (ALL WIRED)
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
# ANALYZE (ENGINE + AI)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    user_id = request.remote_addr
    usage = usage_counter.get(user_id, 0)

    if usage >= FREE_LIMIT:
        return jsonify({"error": "PAYWALL"})

    usage_counter[user_id] = usage + 1

    try:
        data = request.json or {}

        job_description = data.get("job_description", "")
        cv_text = data.get("cv_text", "")

        if not cv_text:
            return jsonify({
                "fit_score": 0,
                "decision": "Error",
                "recruiter_view": "Please upload CV",
                "hiring_manager_view": "CV missing"
            })

        # =========================
        # SCORING ENGINE
        # =========================
        job_tokens = extract_tokens(job_description)
        cv_tokens = extract_tokens(cv_text)

        overlap = job_tokens.intersection(cv_tokens)
        overlap_score = len(overlap)
        mismatch_score = len(job_tokens - cv_tokens)

        score = int((overlap_score * 2) - (mismatch_score * 0.3))
        score = max(0, min(score, 100))

        if score >= 70:
            decision = "Strong Apply"
        elif score >= 40:
            decision = "Consider"
        else:
            decision = "Reject"

        # =========================
        # AI EXPLANATION
        # =========================

        prompt = f"""
You are a professional recruiter and hiring manager.

Evaluate the match between this CV and job description.

Be realistic, direct, and specific.
Do NOT hallucinate.
Do NOT be generic.

CV:
{cv_text[:4000]}

JOB DESCRIPTION:
{job_description[:4000]}

SYSTEM SCORE: {score}
SYSTEM DECISION: {decision}

Respond EXACTLY in this format:

Recruiter View:
<short realistic screening explanation>

Hiring Manager View:
<decision + reasoning + recommendation>
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        text = response.choices[0].message.content

        recruiter_view = ""
        hiring_manager_view = ""

        if "Hiring Manager View:" in text:
            parts = text.split("Hiring Manager View:")
            recruiter_view = parts[0].replace("Recruiter View:", "").strip()
            hiring_manager_view = parts[1].strip()
        else:
            recruiter_view = text
            hiring_manager_view = "Could not parse AI response."

        return jsonify({
            "fit_score": score,
            "decision": decision,
            "recruiter_view": recruiter_view,
            "hiring_manager_view": hiring_manager_view
        })

    except Exception as e:
        return jsonify({
            "fit_score": 0,
            "decision": "Error",
            "recruiter_view": "System error",
            "hiring_manager_view": str(e)
        })

# =========================
# STRIPE CHECKOUT
# =========================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "HiddenEdge Unlock"
                    },
                    "unit_amount": 1900,
                },
                "quantity": 1,
            }],
            success_url=request.host_url + "success",
            cancel_url=request.host_url + "app"
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)