print("=== NEW BACKEND VERSION LOADED ===")

from flask import Flask, request, jsonify, render_template, redirect
import os
import stripe
import docx
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
# HELPERS
# =========================

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return ""

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
# ANALYZE (AI-BASED)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    user_id = request.remote_addr
    usage = usage_counter.get(user_id, 0)

    if usage >= FREE_LIMIT:
        return jsonify({"error": "PAYWALL"})

    usage_counter[user_id] = usage + 1

    try:
        cv_file = request.files.get("cv_file")
        job_description = request.form.get("job_description", "")

        if not cv_file:
            return jsonify({"error": "No CV uploaded"})

        # Extract CV text
        if cv_file.filename.endswith(".docx"):
            cv_text = extract_text_from_docx(cv_file)
        else:
            cv_text = cv_file.read().decode("utf-8", errors="ignore")

        if not cv_text.strip():
            return jsonify({
                "fit_score": 0,
                "decision": "Error",
                "recruiter_view": "CV could not be read properly.",
                "hiring_manager_view": "Invalid CV format."
            })

        # =========================
        # AI ANALYSIS
        # =========================

        prompt = f"""
You are an experienced recruiter and hiring manager.

Compare the following CV and job description.

Return:
- fit_score (0-100)
- decision (Strong Apply / Consider / Reject)
- recruiter_view (natural, human tone, professional)
- hiring_manager_view (executive tone, realistic)
- recommended_roles (if mismatch, suggest better roles)

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}

Respond in JSON format only.
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content

        # Fallback if parsing fails
        try:
            import json
            result = json.loads(content)
        except:
            result = {
                "fit_score": 50,
                "decision": "Consider",
                "recruiter_view": content,
                "hiring_manager_view": content,
                "recommended_roles": []
            }

        return jsonify(result)

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