# =========================================
# HiddenEdge Platform
# SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# =========================================

from flask import Flask, request, jsonify, render_template, send_file, session, redirect
from core.cv.cv_service import CVService

import io
import os
import json
from datetime import timedelta
from docx import Document
import PyPDF2
import stripe

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    AI_ENABLED = True
except:
    AI_ENABLED = False

print("HiddenEdge Engine v1.3 | Monetization Ready")

# =========================================
# APP INIT
# =========================================

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "hiddenedge_dev_secret"
app.permanent_session_lifetime = timedelta(days=30)

cv_service = CVService()

# =========================================
# STRIPE CONFIG
# =========================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL") or "http://127.0.0.1:5000"

# =========================================
# SESSION VALIDATION
# =========================================

def is_valid_session():
    return session.get("user_email") and "usage" in session and "paid" in session

def require_valid_session():
    if not is_valid_session():
        session.clear()
        return False
    return True

def require_paid():
    if not require_valid_session():
        return False
    return session.get("paid", False)

def increment_usage():
    session["usage"] = session.get("usage", 0) + 1

def check_free_limit():
    return (not session.get("paid", False)) and session.get("usage", 0) >= 3

# =========================================
# ROUTES
# =========================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/app")
def app_page():
    if not require_valid_session():
        return redirect("/")
    return render_template("app.html")

@app.route("/submit-email", methods=["POST"])
def submit_email():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False}), 400

    session.permanent = True
    session["user_email"] = email
    session["usage"] = 0
    session["paid"] = False

    return jsonify({"success": True, "redirect": "/app"})

# =========================================
# STRIPE
# =========================================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():

    if not require_valid_session():
        return jsonify({"error": "unauthorized"}), 401

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='subscription',
        line_items=[{'price': STRIPE_PRICE_ID, 'quantity': 1}],
        success_url=f"{BASE_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/app"
    )

    return jsonify({"url": checkout_session.url})


@app.route("/payment-success")
def payment_success():

    if not require_valid_session():
        return redirect("/")

    session_id = request.args.get("session_id")

    if session_id:
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            if checkout_session.payment_status == "paid":
                session["paid"] = True
        except Exception as e:
            print("Stripe error:", e)

    return redirect("/app")

# =========================================
# FILE EXTRACTION
# =========================================

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def extract_text(filename, file_bytes):
    if filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    return ""

# =========================================
# ANALYZE (FREE → PAY AFTER 3)
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    if not require_valid_session():
        return jsonify({"error": "unauthorized"}), 401

    if check_free_limit():
        return jsonify({"error": "payment_required"}), 402

    files = request.files.getlist("files")
    job_text = request.form.get("job_text", "")

    texts = []
    for f in files:
        t = extract_text(f.filename.lower(), f.read())
        if t:
            texts.append(t)

    increment_usage()

    result = cv_service.analyze_cv(texts, job_text)
    result["texts"] = texts

    return jsonify(result)

# =========================================
# EVALUATION (FREE VALUE DRIVER)
# =========================================

@app.route("/evaluate_answers", methods=["POST"])
def evaluate_answers():

    if not require_valid_session():
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    base_score = int(data.get("base_score", 50))
    answers = data.get("answers", "")

    try:
        if AI_ENABLED:
            prompt = f"""
Evaluate how candidate answers improve job fit.

Base score: {base_score}

Answers:
{answers}

Return JSON:
{{
 "improvement": 15,
 "improvement_factors": [
   "Factor 1",
   "Factor 2",
   "Factor 3"
 ]
}}
"""
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            parsed = json.loads(res.choices[0].message.content)

            improvement = min(25, int(parsed.get("improvement", 10)))

            return jsonify({
                "base_score": base_score,
                "improvement": improvement,
                "new_score": min(100, base_score + improvement),
                "improvement_factors": parsed.get("improvement_factors", [])
            })

    except Exception as e:
        print("Eval error:", e)

    return jsonify({
        "base_score": base_score,
        "improvement": 10,
        "new_score": base_score + 10,
        "improvement_factors": [
            "Improved clarity",
            "Better alignment",
            "Stronger positioning"
        ]
    })

# =========================================
# CV IMPROVEMENT (PAID ONLY)
# =========================================

@app.route("/improve_cv", methods=["POST"])
def improve_cv():

    if not require_valid_session():
        return jsonify({"error": "unauthorized"}), 401

    if not require_paid():
        return jsonify({"error": "payment_required"}), 402

    data = request.json

    texts = data.get("texts", [])
    job_text = data.get("job_text", "")
    answers = data.get("answers", [])

    result = cv_service.refine_cv_with_answers(
        texts,
        job_text,
        "\n".join(answers)
    )

    return jsonify({
        "improved_cv": result.get("cv", ""),
        "original_score": 0,
        "new_score": result.get("fit_score", 80),
        "delta": 10
    })

# =========================================
# DOWNLOAD
# =========================================

@app.route("/download_cv", methods=["POST"])
def download_cv():

    if not require_valid_session():
        return jsonify({"error": "unauthorized"}), 401

    if not require_paid():
        return jsonify({"error": "payment_required"}), 402

    data = request.json
    cv_text = data.get("cv_text", "")

    doc = Document()
    for line in cv_text.split("\n"):
        doc.add_paragraph(line)

    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)

    return send_file(stream, as_attachment=True,
                     download_name="HiddenEdge_CV.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)