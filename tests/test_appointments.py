
def test_book_appointment(client, sample_data):
    response = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "booked"


def test_prevent_double_booking(client, sample_data):
    payload = {
        "doctor_id": sample_data["doctor_id"],
        "patient_id": sample_data["patient_id"],
        "start_at": sample_data["slot"],
    }

    first = client.post("/appointments", json=payload)
    second = client.post("/appointments", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_cancel_appointment(client, sample_data):
    booking = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    appointment_id = booking.json()["id"]

    response = client.patch(
        f"/appointments/{appointment_id}/cancel",
        json={"reason": "Patient requested cancellation"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert (
        response.json()["cancellation_reason"]
        == "Patient requested cancellation"
    )


def test_cannot_reschedule_cancelled_appointment(client, sample_data):
    booking = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    appointment_id = booking.json()["id"]

    cancelled = client.patch(
        f"/appointments/{appointment_id}/cancel",
        json={"reason": "No longer needed"},
    )

    assert cancelled.status_code == 200

    response = client.patch(
        f"/appointments/{appointment_id}/reschedule",
        json={"start_at": sample_data["second_slot"]},
    )

    assert response.status_code == 409


def test_patient_upcoming_appointments(client, sample_data):
    booking = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    assert booking.status_code == 201

    response = client.get(
        f"/patients/{sample_data['patient_id']}/appointments"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == booking.json()["id"]


def test_reject_booking_outside_working_hours(client, sample_data):
    response = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": f"{sample_data['date']}T13:00:00+03:00",
        },
    )

    assert response.status_code == 422


def test_reject_booking_in_the_past(client, sample_data):
    response = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": "2020-01-01T09:00:00+03:00",
        },
    )

    assert response.status_code == 422


def test_failed_reschedule_preserves_original_booking(
    client, sample_data
):
    first_booking = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    second_booking = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["second_slot"],
        },
    )

    assert first_booking.status_code == 201
    assert second_booking.status_code == 201

    original_id = first_booking.json()["id"]

    response = client.patch(
        f"/appointments/{original_id}/reschedule",
        json={"start_at": sample_data["second_slot"]},
    )

    assert response.status_code == 409

    # The failed reschedule must not change the original booking.
    original = client.get(
        f"/patients/{sample_data['patient_id']}/appointments"
    )

    assert original.status_code == 200

    appointments = {
        item["id"]: item for item in original.json()
    }

    assert appointments[original_id]["start_at"] == (
        first_booking.json()["start_at"]
    )
    assert appointments[original_id]["status"] == "booked"


def test_cancellation_reopens_the_slot(client, sample_data):
    booking = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    assert booking.status_code == 201

    appointment_id = booking.json()["id"]

    cancellation = client.patch(
        f"/appointments/{appointment_id}/cancel",
        json={"reason": "Patient requested cancellation"},
    )

    assert cancellation.status_code == 200

    # A new patient should be able to book the released slot.
    new_patient = client.post(
        "/appointments",
        json={
            "doctor_id": sample_data["doctor_id"],
            "patient_id": sample_data["patient_id"],
            "start_at": sample_data["slot"],
        },
    )

    assert new_patient.status_code == 201
    assert new_patient.json()["id"] != appointment_id
