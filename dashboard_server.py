from flask import Flask, render_template, request, jsonify, redirect
import os
import stripe
from openai import OpenAI
import json
import re
from io import BytesIO

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
    filename = file.filename.lower()

    if filename.endswith(".docx"):
        from docx import Document
        doc = Document(BytesIO(file.read()))
        return "\n".join([p.text for p in doc.paragraphs])

    elif filename.endswith(".pdf"):
        import PyPDF2
        reader = PyPDF2.PdfReader(BytesIO(file.read()))
        return "\n".join([p.extract_text() or "" for p in reader.pages])

    else:
        return file.read().decode("utf-8", errors="ignore")

# ================= ANALYZE (NESTOR) =================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        job_text = request.form.get("job", "")
        file = request.files.get("file")

        cv_text = extract_cv(file) if file else ""

        prompt = f"""
You are Nestor, a strict hiring evaluator.

You must:
1. Score the match
2. Provide recruiter and hiring manager views
3. If score between 50 and 70 → provide 3 gaps and 3 actions

Return JSON:

{{
  "fit_score": number,
  "recruiter_view": "...",
  "hiring_manager_view": "...",
  "gaps": ["...", "...", "..."],
  "actions": ["...", "...", "..."]
}}

RULES:
- <50 → gaps optional
- >70 → gaps/actions empty []
- No generic advice
- No hallucinations

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
        data = json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group(0))

        score = int(data.get("fit_score", 0))
        decision = map_decision(score)

        return jsonify({
            "cv_text": cv_text,
            "job_text": job_text,
            "nestor": {
                "decision": decision,
                "fit_score": score,
                "recruiter_view": data.get("recruiter_view", ""),
                "hiring_manager_view": data.get("hiring_manager_view", "")
            },
            "gaps": data.get("gaps", []),
            "actions": data.get("actions", [])
        })

    except Exception as e:
        return jsonify({
            "nestor": {
                "decision": "Error",
                "fit_score": 0,
                "recruiter_view": "System error",
                "hiring_manager_view": str(e)
            },
            "gaps": [],
            "actions": []
        }), 500

# ================= ALEC =================

@app.route("/alec", methods=["POST"])
def alec():
    data = request.json
    cv_text = data.get("cv_text", "")
    job_text = data.get("job_text", "")

    prompt = f"""
You are Alec, a senior CV optimization expert.

Rewrite the CV to match the job.

Rules:
- Do NOT invent experience
- Improve clarity and impact
- Align with job keywords
- Keep it professional and structured

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
        "alec_cv": response.choices[0].message.content.strip()
    })

# ================= DOWNLOAD =================

@app.route("/download_cv", methods=["POST"])
def download_cv():
    data = request.json
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

@app.route("/create-checkout-session")
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url="https://hiddenedge-live.onrender.com/app?paid=true",
        cancel_url="https://hiddenedge-live.onrender.com/app",
    )
    return redirect(session.url, code=303)

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)