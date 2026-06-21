import sqlite3
import uuid
from datetime import date
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for


APP_DIR = Path(__file__).parent
DATABASE_PATH = APP_DIR / "event_center.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "local-event-center-change-me"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with sqlite3.connect(DATABASE_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                event_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                guest_count INTEGER NOT NULL,
                event_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'declined')),
                owner_note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def conflicting_bookings(event_date: str, start_time: str, end_time: str, exclude_id: str | None = None):
    query = """
        SELECT * FROM bookings
        WHERE event_date = ?
          AND status IN ('pending', 'approved')
          AND start_time < ?
          AND end_time > ?
    """
    params: list[str] = [event_date, end_time, start_time]
    if exclude_id:
        query += " AND id != ?"
        params.append(exclude_id)
    return get_db().execute(query, params).fetchall()


def validate_booking(form) -> tuple[dict[str, str], list[str]]:
    fields = {
        "client_name": form.get("client_name", "").strip(),
        "email": form.get("email", "").strip().lower(),
        "phone": form.get("phone", "").strip(),
        "event_name": form.get("event_name", "").strip(),
        "event_type": form.get("event_type", "").strip(),
        "guest_count": form.get("guest_count", "").strip(),
        "event_date": form.get("event_date", "").strip(),
        "start_time": form.get("start_time", "").strip(),
        "end_time": form.get("end_time", "").strip(),
        "notes": form.get("notes", "").strip(),
    }
    errors: list[str] = []
    required = ("client_name", "email", "phone", "event_name", "event_type", "guest_count", "event_date", "start_time", "end_time")
    for field in required:
        if not fields[field]:
            errors.append("Please complete every required field.")
            break

    try:
        fields["guest_count"] = str(int(fields["guest_count"]))
        if int(fields["guest_count"]) < 1 or int(fields["guest_count"]) > 350:
            errors.append("Guest count must be between 1 and 350.")
    except ValueError:
        errors.append("Guest count must be a whole number.")

    try:
        requested_date = date.fromisoformat(fields["event_date"])
        if requested_date < date.today():
            errors.append("Please choose a future date.")
    except ValueError:
        errors.append("Please select a valid event date.")

    if fields["start_time"] and fields["end_time"] and fields["start_time"] >= fields["end_time"]:
        errors.append("End time must be later than start time.")

    return fields, errors


@app.route("/")
def home():
    upcoming = get_db().execute(
        """
        SELECT event_date, start_time, end_time, event_name
        FROM bookings
        WHERE status = 'approved' AND event_date >= ?
        ORDER BY event_date, start_time
        LIMIT 4
        """,
        (date.today().isoformat(),),
    ).fetchall()
    return render_template("home.html", upcoming=upcoming, today=date.today().isoformat())


@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        fields, errors = validate_booking(request.form)
        if not errors:
            conflicts = conflicting_bookings(fields["event_date"], fields["start_time"], fields["end_time"])
            if conflicts:
                errors.append("That date and time is currently held. Please choose another time window.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("book.html", form=fields, today=date.today().isoformat())

        booking_id = uuid.uuid4().hex
        get_db().execute(
            """
            INSERT INTO bookings (
                id, client_name, email, phone, event_name, event_type, guest_count,
                event_date, start_time, end_time, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (booking_id, *[fields[key] for key in (
                "client_name", "email", "phone", "event_name", "event_type", "guest_count",
                "event_date", "start_time", "end_time", "notes",
            )]),
        )
        get_db().commit()
        return redirect(url_for("booking_received", booking_id=booking_id))

    return render_template("book.html", form={}, today=date.today().isoformat())


@app.route("/booking-received/<booking_id>")
def booking_received(booking_id: str):
    booking = get_db().execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if booking is None:
        return redirect(url_for("home"))
    return render_template("booking_received.html", booking=booking)


@app.route("/api/availability")
def availability():
    event_date = request.args.get("date", "")
    start_time = request.args.get("start", "")
    end_time = request.args.get("end", "")
    if not event_date or not start_time or not end_time or start_time >= end_time:
        return jsonify({"available": False, "message": "Choose a valid date and time window."}), 400

    conflicts = conflicting_bookings(event_date, start_time, end_time)
    return jsonify({
        "available": not conflicts,
        "message": "This time is available to request." if not conflicts else "This time overlaps an existing request.",
    })


@app.route("/owner")
def owner_dashboard():
    status_filter = request.args.get("status", "pending")
    if status_filter not in {"pending", "approved", "declined", "all"}:
        status_filter = "pending"
    db = get_db()
    if status_filter == "all":
        bookings = db.execute("SELECT * FROM bookings ORDER BY event_date, start_time").fetchall()
    else:
        bookings = db.execute(
            "SELECT * FROM bookings WHERE status = ? ORDER BY event_date, start_time", (status_filter,)
        ).fetchall()
    counts = {
        status: db.execute("SELECT COUNT(*) FROM bookings WHERE status = ?", (status,)).fetchone()[0]
        for status in ("pending", "approved", "declined")
    }
    approved = db.execute(
        "SELECT * FROM bookings WHERE status = 'approved' AND event_date >= ? ORDER BY event_date, start_time",
        (date.today().isoformat(),),
    ).fetchall()
    return render_template(
        "owner.html", bookings=bookings, counts=counts, status_filter=status_filter, approved=approved
    )


@app.route("/owner/bookings/<booking_id>/decision", methods=["POST"])
def booking_decision(booking_id: str):
    action = request.form.get("action")
    owner_note = request.form.get("owner_note", "").strip()
    booking = get_db().execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if booking is None or action not in {"approved", "declined"}:
        return redirect(url_for("owner_dashboard"))

    if action == "approved":
        conflicts = conflicting_bookings(booking["event_date"], booking["start_time"], booking["end_time"], booking_id)
        if conflicts:
            flash("Approval blocked: this request now conflicts with an existing booking.", "error")
            return redirect(url_for("owner_dashboard", status="pending"))

    get_db().execute(
        "UPDATE bookings SET status = ?, owner_note = ? WHERE id = ?",
        (action, owner_note, booking_id),
    )
    get_db().commit()
    flash(f"Booking {action}.", "success")
    return redirect(url_for("owner_dashboard", status="pending"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5053)
