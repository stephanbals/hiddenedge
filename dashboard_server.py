# =========================================
# HiddenEdge Platform
# SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
# =========================================

from flask import Flask, request, jsonify, render_template, send_file, session, redirect
from core.cv.cv_service import CVService
from core.cv.outcome_service import OutcomeService

import io
import os
from datetime import timedelta
from docx import Document
import PyPDF2
import stripe

print("HiddenEdge Engine v1.1 | SB3PM")

# =========================================
# APP INIT
# =========================================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.secret_key = "hiddenedge_dev_secret"
app.permanent_session_lifetime = timedelta(days=30)

cv_service = CVService()
outcome_service = OutcomeService()

# =========================================
# STRIPE CONFIG
# =========================================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL") or "http://127.0.0.1:5000"

# =========================================
# AUTH HELPERS
# =========================================

def require_user():
    return session.get("user_email") is not None


def require_paid_or_free():
    if not require_user():
        return jsonify({"error": "unauthorized"}), 401

    usage = session.get("usage", 0)
    paid = session.get("paid", False)

    if not paid and usage >= 3:
        return jsonify({"error": "payment_required"}), 402

    return None


def increment_usage():
    session["usage"] = session.get("usage", 0) + 1


# =========================================
# ROUTES
# =========================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/app")
def app_page():
    if not require_user():
        return redirect("/")
    return render_template("app.html")


@app.route("/eula")
def eula():
    return render_template("eula.html")


@app.route("/email")
def email():
    return render_template("email.html")


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
# STRIPE CHECKOUT
# =========================================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():

    if not require_user():
        return jsonify({"error": "unauthorized"}), 401

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            success_url=f"{BASE_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/payment-cancel",
        )

        return jsonify({"url": checkout_session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================
# 🔒 SECURE PAYMENT SUCCESS (NO BYPASS)
# =========================================

@app.route("/payment-success")
def payment_success():

    if not require_user():
        return redirect("/")

    session_id = request.args.get("session_id")

    if not session_id:
        return redirect("/app")

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # 🔥 VERIFY PAYMENT STATUS
        if checkout_session.payment_status == "paid":
            session["paid"] = True
        else:
            session["paid"] = False

    except Exception as e:
        print("Stripe verification error:", e)
        session["paid"] = False

    return render_template("success.html")


@app.route("/payment-cancel")
def payment_cancel():
    return render_template("payment-cancel.html")


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
# 🔒 ANALYZE (PAYWALL ENFORCED)
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    if not require_user():
        return jsonify({"error": "unauthorized"}), 401

    # 🔥 HARD PAYWALL CHECK
    auth = require_paid_or_free()
    if auth:
        return auth

    files = request.files.getlist("files")
    job_text = request.form.get("job_text", "")

    texts = []
    for f in files:
        t = extract_text(f.filename.lower(), f.read())
        if t:
            texts.append(t)

    # 🔥 COUNT USAGE
    increment_usage()

    result = cv_service.analyze_cv(texts, job_text)
    result["texts"] = texts

    return jsonify(result)


# =========================================
# SCORE INTELLIGENCE
# =========================================

@app.route("/evaluate_answers", methods=["POST"])
def evaluate_answers():

    if not require_user():
        return jsonify({"error": "unauthorized"}), 401

    data = request.json

    base_score = int(data.get("base_score", 50))
    answers = data.get("answers", "")

    length_score = min(15, len(answers) // 30)
    keywords = ["impact", "result", "delivered", "improved", "managed"]
    relevance_score = sum([1 for k in keywords if k in answers.lower()])

    improvement = min(25, length_score + relevance_score)
    new_score = min(100, base_score + improvement)

    return jsonify({
        "base_score": base_score,
        "improvement": improvement,
        "new_score": new_score
    })


# =========================================
# 🔒 IMPROVE CV (PAYWALL)
# =========================================

@app.route("/improve_cv", methods=["POST"])
def improve_cv():

    if not require_user():
        return jsonify({"error": "unauthorized"}), 401

    auth = require_paid_or_free()
    if auth:
        return auth

    data = request.json

    texts = data.get("texts", [])
    job_text = data.get("job_text", "")
    answers = data.get("answers", [])

    if not texts or not job_text:
        return jsonify({"error": "Missing input"}), 400

    try:
        increment_usage()

        base = cv_service.analyze_cv(texts, job_text)
        base_score = base.get("fit_score", 60)

        improved = cv_service.refine_cv_with_answers(
            texts,
            job_text,
            "\n".join(answers)
        )

        improved_cv = improved.get("cv", "")
        new_score = improved.get("fit_score", base_score + 10)
        delta = new_score - base_score

        return jsonify({
            "improved_cv": improved_cv,
            "original_score": base_score,
            "new_score": new_score,
            "delta": delta
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================
# DOWNLOAD CV
# =========================================

@app.route("/download_cv", methods=["POST"])
def download_cv():

    if not require_user():
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    cv_text = data.get("cv_text", "")

    doc = Document()
    for line in cv_text.split("\n"):
        doc.add_paragraph(line)

    stream = io.BytesIO()
    doc.save(stream)
    stream.seek(0)

    return send_file(
        stream,
        as_attachment=True,
        download_name="HiddenEdge_CV.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# =========================================
# OUTCOME LAYER
# =========================================

@app.route("/track_application", methods=["POST"])
def track_application():
    return jsonify(outcome_service.track_application(request.json))


@app.route("/update_result", methods=["POST"])
def update_result():
    data = request.json
    return jsonify(
        outcome_service.update_result(data.get("index"), data.get("result"))
    )


@app.route("/analyze_outcomes", methods=["GET"])
def analyze_outcomes():
    return jsonify(outcome_service.analyze())


# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)