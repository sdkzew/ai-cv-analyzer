import os
import sys
import threading
import webview
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from analyzer.extractor import extract_text
from analyzer.ats_scorer import score_cv
from analyzer.matcher import match_job
from analyzer.suggestions import generate_suggestions


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


UPLOAD_FOLDER = os.path.join(os.path.expanduser("~"), ".cv-analyzer-uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
PORT = 5000

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
app.secret_key = "cv-analyzer-secret-2024"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    if "cv_file" not in request.files:
        flash("Nu ai selectat niciun fisier.")
        return redirect(url_for("index"))

    file = request.files["cv_file"]
    if file.filename == "":
        flash("Nu ai selectat niciun fisier.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Format nesuportat. Uploadeaza un fisier PDF sau DOCX.")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        cv_text = extract_text(filepath)
        if not cv_text.strip():
            flash("Nu s-a putut extrage text din fisier. Incearca un alt PDF sau DOCX.")
            return redirect(url_for("index"))

        job_description = request.form.get("job_description", "").strip()

        ats_result = score_cv(cv_text)
        match_result = match_job(cv_text, job_description)
        suggestions = generate_suggestions(
            cv_text, ats_result.score, match_result.score, match_result.missing_keywords
        )

        return render_template(
            "results.html",
            ats=ats_result,
            match=match_result,
            suggestions=suggestions,
            has_job=bool(job_description),
            word_count=len(cv_text.split()),
        )
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


def start_flask():
    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Start Flask in background thread
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()

    # Open native window (no browser)
    webview.create_window(
        title="AI CV Analyzer",
        url=f"http://127.0.0.1:{PORT}",
        width=900,
        height=750,
        min_size=(700, 600),
        resizable=True,
    )
    webview.start()
