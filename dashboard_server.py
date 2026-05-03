# =========================================
# HiddenEdge — FULL SERVER (FINAL)
# ANALYZE + REFINE + POSTGRES STORAGE
# =========================================

import os
import psycopg2
from flask import Flask, request, jsonify, render_template, redirect, session

from core.cv.cv_service import CVService
from core.scoring.fit_engine import evaluate_fit
from core.scoring.reasoning_engine import build_reasoning
from core.crawler.multi_source_provider import fetch_all_jobs

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

# =========================================
# DATABASE
# =========================================

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL)


def save_cv(email, original_cv, improved_cv, job_text):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO user_cvs (email, original_cv, improved_cv, job_text)
            VALUES (%s, %s, %s, %s)
        """, (email, original_cv, improved_cv, job_text))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print("DB ERROR:", e)


# =========================================
# ROUTES
# =========================================

@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/eula")
def eula():
    return render_template("eula.html")


@app.route("/email")
def email():
    return render_template("email.html")


@app.route("/submit-email", methods=["POST"])
def submit_email():

    data = request.get_json()
    email = data.get("email") if data else None

    if not email:
        return jsonify({"error": "Email required"}), 400

    session["user_email"] = email
    session.modified = True

    return jsonify({"redirect": "/app"})


@app.route("/app")
def app_page():
    if not session.get("user_email"):
        return redirect("/email")

    return render_template("app.html")


# =========================================
# ANALYZE
# =========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    files = request.files.getlist("files")
    job_text = request.form.get("job_text", "")

    if not files:
        return jsonify({"error": "No CV uploaded"}), 400

    cv_texts = []

    for f in files:
        try:
            content = f.read().decode("utf-8", errors="ignore")
            cv_texts.append(content)
        except:
            continue

    full_cv = "\n\n".join(cv_texts)

    # ENGINE SCORE
    fit_result = evaluate_fit(full_cv, job_text)

    # LLM
    service = CVService()
    ai_data = service.analyze_cv(cv_texts, job_text)

    # MERGE SCORE
    final_score = int(
        (fit_result.get("fit_score", 0) * 0.5) +
        (ai_data.get("fit_score", 0) * 0.5)
    )

    ai_data["fit_score"] = final_score

    # SAFE STRUCTURE
    ai_data.setdefault("ats_analysis", {"matches": []})
    ai_data.setdefault("recruiter_view", {})
    ai_data.setdefault("hiring_manager_view", {})
    ai_data.setdefault("questions", [])

    return jsonify(ai_data)


# =========================================
# 🔥 REFINE CV (NEW)
# =========================================

@app.route("/refine", methods=["POST"])
def refine():

    files = request.files.getlist("files")
    job_text = request.form.get("job_text", "")
    answers = request.form.getlist("answers")

    if not files:
        return jsonify({"error": "No CV uploaded"}), 400

    cv_texts = []

    for f in files:
        try:
            content = f.read().decode("utf-8", errors="ignore")
            cv_texts.append(content)
        except:
            continue

    full_cv = "\n\n".join(cv_texts)

    service = CVService()

    result = service.refine_cv_with_answers(
        cv_texts,
        job_text,
        answers
    )

    improved_cv = result.get("cv", "")

    # =========================================
    # 🔥 STORE IN DB
    # =========================================

    email = session.get("user_email", "anonymous")

    save_cv(email, full_cv, improved_cv, job_text)

    return jsonify({
        "cv": improved_cv,
        "fit_score": result.get("fit_score", 75)
    })


# =========================================
# JOB SEARCH
# =========================================

@app.route("/find_jobs", methods=["POST"])
def find_jobs():

    data = request.get_json() or {}
    role = data.get("role", "project manager")

    try:
        jobs = fetch_all_jobs(role)
        return jsonify({"jobs": jobs[:20]})

    except Exception as e:
        print("JOB ERROR:", e)

        return jsonify({"jobs": []})


# =========================================
# STRIPE (UNCHANGED)
# =========================================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    return jsonify({"url": "https://checkout.stripe.com/test"})


@app.route("/create-portal-session", methods=["POST"])
def create_portal_session():
    return jsonify({"url": "https://billing.stripe.com/test"})


# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)