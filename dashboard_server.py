from flask import Flask, render_template, request, jsonify, redirect
import os
import stripe
from openai import OpenAI
import json
import re
from io import BytesIO

# ===== INIT =====
app = Flask(__name__, static_folder="static", template_folder="templates")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

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

# ================= DECISION MAPPING =================

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

# ================= ANALYZE =================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        job_text = request.form.get("job", "")
        file = request.files.get("file")

        cv_text = ""

        if file:
            filename = file.filename.lower()

            if filename.endswith(".docx"):
                from docx import Document
                doc = Document(BytesIO(file.read()))
                cv_text = "\n".join([p.text for p in doc.paragraphs])

            elif filename.endswith(".pdf"):
                import PyPDF2
                reader = PyPDF2.PdfReader(BytesIO(file.read()))
                pages = []
                for page in reader.pages:
                    try:
                        pages.append(page.extract_text() or "")
                    except:
                        pass
                cv_text = "\n".join(pages)

            else:
                cv_text = file.read().decode("utf-8", errors="ignore")

        if not cv_text.strip():
            cv_text = "No CV content detected"

        # ===== NESTOR PROMPT =====
        prompt = f"""
You are Nestor, a strict hiring evaluator.

Return ONLY JSON:

{{
  "fit_score": number,
  "recruiter_view": "...",
  "hiring_manager_view": "..."
}}

RULES:
- If domain mismatch → score MUST be below 20
- No inflated scoring
- Be realistic and critical

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

        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
        else:
            raise Exception("No JSON returned")

        score = int(data.get("fit_score", 0))

        # ===== DECISION MAPPING =====
        decision = map_decision(score)

        # ===== SOFTEN OVER-HARSH TEXT =====
        recruiter_view = data.get("recruiter_view", "")
        hiring_manager_view = data.get("hiring_manager_view", "")

        if score >= 70:
            hiring_manager_view += " Overall, the candidate appears capable with limited adaptation required."

        return jsonify({
            "nestor": {
                "decision": decision,
                "fit_score": score,
                "recruiter_view": recruiter_view,
                "hiring_manager_view": hiring_manager_view
            }
        })

    except Exception as e:
        print("ANALYZE ERROR:", str(e))

        return jsonify({
            "nestor": {
                "decision": "Error",
                "fit_score": 0,
                "recruiter_view": "System error",
                "hiring_manager_view": str(e)
            }
        }), 500

# ================= STRIPE =================

@app.route("/create-checkout-session")
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url="https://hiddenedge-live.onrender.com/app?paid=true",
            cancel_url="https://hiddenedge-live.onrender.com/app",
        )

        return redirect(session.url, code=303)

    except Exception as e:
        return f"Stripe error: {str(e)}", 500

# ================= NO CACHE =================

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)