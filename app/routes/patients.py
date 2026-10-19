
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models import Appointment, Patient
from app.schemas.appointment import AppointmentResponse
from app.services.appointment_service import BookingError


router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "/{patient_id}/appointments",
    response_model=list[AppointmentResponse],
)
def get_patient_appointments(
    patient_id: int,
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise BookingError(404, "Patient not found.")

    now = datetime.now(timezone.utc)

    query = (
        select(Appointment)
        .where(
            Appointment.patient_id == patient_id,
            Appointment.status == "booked",
            Appointment.start_at > now,
        )
        .order_by(Appointment.start_at.asc())
    )

    return db.scalars(query).all()
