import os
import sqlite3
import uuid
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, g

app = Flask(__name__)
app.secret_key = "change-this-in-production"

DB_PATH = Path(__file__).parent / "fundraiser.db"
UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id        TEXT PRIMARY KEY,
            name      TEXT NOT NULL,
            email     TEXT NOT NULL,
            cause     TEXT NOT NULL,
            goal      REAL NOT NULL,
            photo     TEXT,
            status    TEXT NOT NULL DEFAULT 'pending',
            note      TEXT,
            created   TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    db.commit()
    db.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Submit ────────────────────────────────────────────────────────────────────

@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        cause = request.form.get("cause", "").strip()
        goal  = request.form.get("goal", "").strip()
        photo_file = request.files.get("photo")

        errors = []
        if not name:  errors.append("Name is required.")
        if not email: errors.append("Email is required.")
        if not cause: errors.append("Please describe your cause.")
        try:
            goal = float(goal)
            if goal <= 0:
                errors.append("Goal must be a positive number.")
        except (ValueError, TypeError):
            errors.append("Please enter a valid goal amount.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("submit.html", form=request.form)

        # Save photo
        photo_filename = None
        if photo_file and photo_file.filename and allowed_file(photo_file.filename):
            ext = photo_file.filename.rsplit(".", 1)[1].lower()
            photo_filename = f"{uuid.uuid4().hex}.{ext}"
            photo_file.save(UPLOAD_DIR / photo_filename)

        req_id = uuid.uuid4().hex
        db = get_db()
        db.execute(
            "INSERT INTO requests (id, name, email, cause, goal, photo) VALUES (?,?,?,?,?,?)",
            (req_id, name, email, cause, goal, photo_filename),
        )
        db.commit()

        return redirect(url_for("submitted", req_id=req_id))

    return render_template("submit.html", form={})


@app.route("/submitted/<req_id>")
def submitted(req_id):
    return render_template("submitted.html", req_id=req_id)


# ── Status check ──────────────────────────────────────────────────────────────

@app.route("/status", methods=["GET", "POST"])
def status():
    results = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if email:
            rows = get_db().execute(
                "SELECT * FROM requests WHERE email = ? ORDER BY created DESC", (email,)
            ).fetchall()
            results = rows

    return render_template("status.html", results=results, email=email)


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.route("/admin")
def admin():
    status_filter = request.args.get("filter", "all")
    db = get_db()
    if status_filter == "all":
        rows = db.execute("SELECT * FROM requests ORDER BY created DESC").fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM requests WHERE status = ? ORDER BY created DESC",
            (status_filter,)
        ).fetchall()
    counts = {
        "all":      db.execute("SELECT COUNT(*) FROM requests").fetchone()[0],
        "pending":  db.execute("SELECT COUNT(*) FROM requests WHERE status='pending'").fetchone()[0],
        "approved": db.execute("SELECT COUNT(*) FROM requests WHERE status='approved'").fetchone()[0],
        "denied":   db.execute("SELECT COUNT(*) FROM requests WHERE status='denied'").fetchone()[0],
    }
    return render_template("admin.html", rows=rows, filter=status_filter, counts=counts)


@app.route("/admin/action/<req_id>", methods=["POST"])
def admin_action(req_id):
    action = request.form.get("action")
    note   = request.form.get("note", "").strip()
    if action in ("approved", "denied"):
        get_db().execute(
            "UPDATE requests SET status = ?, note = ? WHERE id = ?",
            (action, note, req_id)
        )
        get_db().commit()
        flash(f"Request {action}.", "success")
    return redirect(url_for("admin", filter=request.args.get("filter", "all")))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5050)
