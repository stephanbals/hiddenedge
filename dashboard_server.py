from flask import Flask, request, jsonify, send_file, redirect, render_template
from core.cv.cv_service import CVService
import zipfile
import io
import os
import re

from docx import Document
import PyPDF2
from openai import OpenAI
import stripe

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

app = Flask(__name__)
cv_service = CVService()

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
    return render_template("index.html")

# 🚨 CRITICAL FIX: prevent caching
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response