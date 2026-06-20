import os
import uuid
import threading
import traceback
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

from resume_parser import parse_resume
from job_fetcher import fetch_all_jobs
from scorer import analyze_resume, score_all_jobs

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MIN_TARGET_RESULTS = 20

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory job store: job_id -> {status, progress, message, profile, results, error}
jobs: dict[str, dict] = {}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process(job_id: str, filepath: str):
    state = jobs[job_id]

    def cb(msg: str, pct: int):
        state["message"] = msg
        state["progress"] = pct

    try:
        # 1. Parse resume
        cb("Parsing resume…", 5)
        resume_text = parse_resume(filepath)

        # 2. Extract a lightweight product profile from the resume
        cb("Analyzing your skills and experience…", 12)
        profile = analyze_resume(resume_text)
        state["profile"] = profile

        target_roles = profile.get("target_titles", ["Software Engineer"])
        skills = profile.get("skills", [])

        # 3. Fetch jobs concurrently
        cb("Searching Series C/D startup job boards…", 20)
        raw_jobs = fetch_all_jobs(target_roles, skills, progress_cb=cb)

        # 4. Score
        cb(f"Found {len(raw_jobs)} jobs — scoring against your profile…", 81)
        top_jobs = score_all_jobs(profile, raw_jobs, progress_cb=cb, top_n=50)

        if len(top_jobs) < MIN_TARGET_RESULTS:
            cb(
                f"Only found {len(top_jobs)} strict Series C/D matches — adding adjacent late-stage startups…",
                88,
            )
            broader_jobs = fetch_all_jobs(
                target_roles,
                skills,
                progress_cb=cb,
                stage_focus=("Series C/D", "Late-stage startup"),
            )
            cb(f"Found {len(broader_jobs)} broader startup jobs — rescoring…", 92)
            top_jobs = score_all_jobs(profile, broader_jobs, progress_cb=cb, top_n=50)

        state["results"] = top_jobs
        state["status"] = "complete"
        state["progress"] = 100
        state["message"] = f"Done! Showing top {len(top_jobs)} matches."

    except Exception:
        state["status"] = "error"
        state["error"] = traceback.format_exc()
        state["message"] = "Something went wrong. See error details."

    finally:
        try:
            os.remove(filepath)
        except Exception:
            pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["resume"]
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Upload a PDF, DOCX, or TXT."}), 400

    job_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower()
    filepath = os.path.join(UPLOAD_FOLDER, f"{job_id}.{ext}")
    file.save(filepath)

    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Starting…",
        "profile": None,
        "results": [],
        "error": None,
    }

    t = threading.Thread(target=process, args=(job_id, filepath), daemon=True)
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id: str):
    if job_id not in jobs:
        return jsonify({"error": "Not found"}), 404
    state = jobs[job_id]
    return jsonify({
        "status": state["status"],
        "progress": state["progress"],
        "message": state["message"],
        "profile": state.get("profile"),
        "error": state.get("error"),
    })


@app.route("/results/<job_id>")
def results(job_id: str):
    if job_id not in jobs:
        return redirect("/")
    state = jobs[job_id]
    if state["status"] != "complete":
        return redirect(f"/loading/{job_id}")
    return render_template("results.html", job_id=job_id, jobs=state["results"], profile=state["profile"])


@app.route("/loading/<job_id>")
def loading(job_id: str):
    if job_id not in jobs:
        return redirect("/")
    return render_template("loading.html", job_id=job_id)


if __name__ == "__main__":
    app.run(debug=True, port=5051, threaded=True)
