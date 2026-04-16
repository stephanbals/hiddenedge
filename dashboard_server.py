from flask import Flask, request, jsonify, send_file
import stripe
import os
import sqlite3
from io import BytesIO

# 🔥 IMPORT YOUR REAL ENGINE
from core.cv.cv_service import extract_text_from_files, evaluate_fit, tailor_cv
from core.cv.doc_export import generate_docx

app = Flask(__name__)

# =========================
# CONFIG
# =========================

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
DB_FILE = "app.db"
FREE_LIMIT = 3

# =========================
# DB INIT
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            usage_count INTEGER DEFAULT 0,
            customer_id TEXT,
            subscription_status TEXT,
            eula_accepted INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# ANALYZE (REAL ENGINE)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():

    email = request.form.get("email")
    job = request.form.get("job")
    files = request.files.getlist("files")

    # =========================
    # ACCESS CONTROL
    # =========================

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT usage_count, subscription_status FROM users WHERE email=?", (email,))
    row = c.fetchone()

    if not row:
        c.execute("INSERT INTO users (email) VALUES (?)", (email,))
        usage = 0
        paid = False
    else:
        usage, sub = row
        paid = sub == "active"

    if not paid and usage >= FREE_LIMIT:
        conn.close()
        return jsonify({"blocked": True})

    if not paid:
        c.execute("UPDATE users SET usage_count = usage_count + 1 WHERE email=?", (email,))
        conn.commit()

    conn.close()

    # =========================
    # CORE ENGINE
    # =========================

    texts = extract_text_from_files(files)

    evaluation = evaluate_fit(texts, job)
    tailored_cv = tailor_cv(texts, job, evaluation)

    return jsonify({
        "blocked": False,
        "nestor": evaluation,
        "alec": {
            "cv": tailored_cv
        }
    })

# =========================
# DOWNLOAD DOCX (REAL)
# =========================

@app.route("/download_cv", methods=["POST"])
def download_cv():

    cv_text = request.json.get("cv")

    file_bytes = generate_docx(cv_text)

    return send_file(
        BytesIO(file_bytes),
        as_attachment=True,
        download_name="HiddenEdge_CV.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)