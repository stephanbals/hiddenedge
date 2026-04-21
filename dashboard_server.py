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

# ================= ANALYZE =================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        job_text = request.form.get("job", "")
        file = request.files.get("file")

        cv_text = ""

        if file:
            filename = file.filename.lower()

            # ===== DOCX SAFE READ =====
            if filename.endswith(".docx"):
                from docx import Document
                doc = Document(BytesIO(file.read()))
                cv_text = "\n".join([p.text for p in doc.paragraphs])

            # ===== PDF SAFE READ =====
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

            # ===== TEXT FALLBACK =====
            else:
                cv_text = file.read().decode("utf-8", errors="ignore")

        if not cv_text.strip():
            cv_text = "No CV content detected"

        # ===== NESTOR PROMPT =====
        prompt = f"""
You are Nestor, a ruthless senior hiring evaluator.

You evaluate CV vs job from TWO perspectives:

1. Recruiter → screening, keywords, fit
2. Hiring Manager → real capability, execution ability

STRICT RULES:
- If domain mismatch → score MUST be below 20
- No politeness
- No generic filler
- No inflated scoring
- Be direct and critical

Return ONLY valid JSON:

{{
  "decision": "...",
  "fit_score": number,
  "recruiter_view": "...",
  "hiring_manager_view": "..."
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

        # ===== HARD JSON EXTRACTION =====
        match = re.search(r"\{.*\}", raw, re.DOTALL)

        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
        else:
            raise Exception("No JSON returned from model")

        return jsonify({"nestor": data})

    except Exception as e:
        print("ANALYZE ERROR:", str(e))

        return jsonify({
            "nestor": {
                "decision": "Error",
                "fit_score": 0,
                "recruiter_view": "System error during evaluation",
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