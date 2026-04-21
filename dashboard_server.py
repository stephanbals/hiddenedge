from flask import Flask, render_template, request, jsonify, redirect
import os
import stripe
from openai import OpenAI
import json
from io import BytesIO

print("=== NEW BACKEND VERSION LOADED ===")

app = Flask(__name__, static_folder="static", template_folder="templates")

# ===== INIT =====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

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
        job_text = request.form.get("job_text", "")
        file = request.files.get("file")

        cv_text = extract_cv(file)

        prompt = f"""
You are Nestor, a strict hiring evaluator.

Return ONLY valid JSON. No explanation.

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
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        raw = response.choices[0].message.content

        print("=== RAW GPT OUTPUT ===")
        print(raw)

        data = json.loads(raw)

        if not isinstance(data, dict):
            raise Exception("Parsed JSON is not a dict")

        score = int(data.get("fit_score", 0))
        decision = map_decision(score)

        return jsonify({
            "nestor": {
                "decision": decision,
                "fit_score": score,
                "recruiter_view": data.get("recruiter_view", ""),
                "hiring_manager_view": data.get("hiring_manager_view", "")
            }
        })

    except Exception as e:
        print("=== ERROR ===", str(e))

        return jsonify({
            "nestor": {
                "decision": "Error",
                "fit_score": 0,
                "recruiter_view": "System error",
                "hiring_manager_view": str(e)
            }
        }), 200

# ================= STRIPE =================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url=f"{BASE_URL}/app?paid=true",
            cancel_url=f"{BASE_URL}/app",
        )
        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= NO CACHE =================

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)