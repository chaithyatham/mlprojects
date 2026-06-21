from datetime import date, timedelta

import pytest

import app as event_app


@pytest.fixture()
def client(tmp_path):
    event_app.DATABASE_PATH = tmp_path / "event_center.db"
    event_app.app.config.update(TESTING=True, SECRET_KEY="test")
    event_app.init_db()
    with event_app.app.test_client() as test_client:
        yield test_client


def booking_payload(**overrides):
    event_date = (date.today() + timedelta(days=14)).isoformat()
    payload = {
        "client_name": "Jordan Lee",
        "email": "jordan@example.com",
        "phone": "555-123-4567",
        "event_name": "Product Launch",
        "event_type": "Corporate event",
        "guest_count": "120",
        "event_date": event_date,
        "start_time": "17:00",
        "end_time": "21:00",
        "notes": "Needs a projector.",
    }
    payload.update(overrides)
    return payload


def test_booking_request_holds_time_and_blocks_overlap(client):
    first = client.post("/book", data=booking_payload(), follow_redirects=True)
    assert first.status_code == 200
    assert b"held for review" in first.data

    overlapping = client.post(
        "/book",
        data=booking_payload(client_name="Casey Ray", start_time="20:00", end_time="22:00"),
        follow_redirects=True,
    )
    assert b"currently held" in overlapping.data


def test_availability_api_reports_conflict(client):
    payload = booking_payload()
    client.post("/book", data=payload)

    response = client.get(
        "/api/availability",
        query_string={"date": payload["event_date"], "start": "18:00", "end": "19:00"},
    )
    assert response.status_code == 200
    assert response.get_json()["available"] is False


def test_owner_cannot_approve_overlapping_requests(client):
    first_payload = booking_payload(event_name="First event")
    client.post("/book", data=first_payload)
    db = event_app.get_db()
    first_id = db.execute("SELECT id FROM bookings").fetchone()[0]
    client.post(f"/owner/bookings/{first_id}/decision", data={"action": "approved"})

    second_id = "manual-overlap"
    db = event_app.get_db()
    db.execute(
        """
        INSERT INTO bookings (
            id, client_name, email, phone, event_name, event_type, guest_count,
            event_date, start_time, end_time, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (second_id, "Taylor", "taylor@example.com", "555", "Overlap", "Other", 10,
         first_payload["event_date"], "20:00", "22:00"),
    )
    db.commit()

    response = client.post(
        f"/owner/bookings/{second_id}/decision", data={"action": "approved"}, follow_redirects=True
    )
    assert b"Approval blocked" in response.data
