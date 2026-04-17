from flask import Flask, request, jsonify, send_file, render_template
import os
import sqlite3
from io import BytesIO
import stripe
import json

from core.cv.cv_service import (
    extract_text_from_files,
    evaluate_fit,
    tailor_cv,
    simulate_improvement,
    regenerate_from_simulation
)
from core.cv.doc_export import generate_docx
from core.cv.report_export import generate_report_pdf

app = Flask(__name__, template_folder="templates")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL")

DB_FILE = "app.db"

# -------------------------------
# DB INIT
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            subscription_status TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            email TEXT,
            cv_text TEXT,
            job TEXT,
            improvements TEXT,
            evaluation TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()


# -------------------------------
# DB HELPERS
# -------------------------------
def activate_user(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO users(email, subscription_status)
        VALUES(?, 'active')
    """, (email,))

    conn.commit()
    conn.close()


def is_paid(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT subscription_status FROM users WHERE email=?", (email,))
    row = c.fetchone()

    conn.close()
    return row and row[0] == "active"


def save_session(email, cv_text, job, evaluation):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("DELETE FROM sessions WHERE email=?", (email,))
    c.execute("""
        INSERT INTO sessions(email, cv_text, job, evaluation)
        VALUES(?,?,?,?)
    """, (email, cv_text, job, json.dumps(evaluation)))

    conn.commit()
    conn.close()


def update_improvements(email, improvements):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        UPDATE sessions SET improvements=?
        WHERE email=?
    """, (json.dumps(improvements), email))

    conn.commit()
    conn.close()


def load_session(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT cv_text, job, improvements, evaluation
        FROM sessions WHERE email=?
    """, (email,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "cv_text": row[0],
        "job": row[1],
        "improvements": json.loads(row[2] or "[]"),
        "evaluation": json.loads(row[3] or "{}")
    }


# -------------------------------
# ROUTES
# -------------------------------

@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/app")
def app_page():
    return render_template("app.html")


# -------------------------------
# ANALYZE
# -------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():

    email = request.form.get("email")
    job = request.form.get("job")
    files = request.files.getlist("files")

    texts = extract_text_from_files(files)
    cv_text = "\n".join(texts)

    evaluation = evaluate_fit(texts, job)
    cv = tailor_cv(texts, job, evaluation)

    save_session(email, cv_text, job, evaluation)

    return jsonify({
        "nestor": evaluation,
        "alec": {"cv": cv}
    })


# -------------------------------
# SIMULATE
# -------------------------------

@app.route("/simulate", methods=["POST"])
def simulate():

    email = request.json.get("email")

    session = load_session(email)
    if not session:
        return jsonify({"error": "No session found"})

    result = simulate_improvement(
        [session["cv_text"]],
        session["job"],
        session["evaluation"]
    )

    update_improvements(email, result.get("improvements_applied", []))

    return jsonify(result)


# -------------------------------
# REGENERATE (PAYWALLED)
# -------------------------------

@app.route("/regenerate", methods=["POST"])
def regenerate():

    email = request.json.get("email")

    if not is_paid(email):
        return jsonify({"paywall": True})

    session = load_session(email)
    if not session:
        return jsonify({"error": "Session missing"})

    new_cv = regenerate_from_simulation(
        [session["cv_text"]],
        session["job"],
        session["improvements"]
    )

    return jsonify({"cv": new_cv})


# -------------------------------
# STRIPE CHECKOUT
# -------------------------------

@app.route("/create_checkout", methods=["POST"])
def create_checkout():

    email = request.json.get("email")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=email,
        line_items=[{
            "price": "price_1TKFETRsFYMAfQV15jNJ365D",
            "quantity": 1
        }],
        success_url=BASE_URL + "/app?paid=true",
        cancel_url=BASE_URL + "/app"
    )

    return jsonify({"url": session.url})


# -------------------------------
# WEBHOOK
# -------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    payload = request.data
    sig = request.headers.get("Stripe-Signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
    except:
        return "fail", 400

    if event["type"] == "checkout.session.completed":
        email = event["data"]["object"]["customer_email"]
        activate_user(email)

    return "ok", 200


# -------------------------------
# DOWNLOAD REPORT
# -------------------------------

@app.route("/download_report", methods=["POST"])
def download_report():

    email = request.json.get("email")
    session = load_session(email)

    pdf_bytes = generate_report_pdf(session["evaluation"])

    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name="HiddenEdge_Report.pdf",
        mimetype="application/pdf"
    )


# -------------------------------
# DOWNLOAD CV
# -------------------------------

@app.route("/download_cv", methods=["POST"])
def download_cv():

    cv = request.json.get("cv")
    template = request.json.get("template")

    file_bytes = generate_docx(cv, template)

    return send_file(
        BytesIO(file_bytes),
        as_attachment=True,
        download_name="HiddenEdge_CV.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


if __name__ == "__main__":
    app.run(debug=True)