
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, Doctor, DoctorWorkingHours, Patient


SLOT_MINUTES = 30


class BookingError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def get_doctor_or_raise(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)

    if doctor is None or not doctor.is_active:
        raise BookingError(404, "Doctor not found or inactive.")

    return doctor


def validate_slot(
    db: Session,
    doctor_id: int,
    start_at: datetime,
    exclude_appointment_id: int | None = None,
) -> None:
    """Validate a proposed appointment slot without creating it."""
    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise BookingError(422, "Appointment time must include a timezone.")

    start_at = start_at.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)

    if start_at <= now:
        raise BookingError(422, "Appointment must be in the future.")

    # Prevent bookings within the next hour.
    if start_at < now + timedelta(hours=1):
        raise BookingError(
            422, "Appointments must be booked at least one hour in advance."
        )

    # Appointment times must fall on 30-minute boundaries.
    if start_at.minute not in (0, 30) or start_at.second != 0 or start_at.microsecond != 0:
        raise BookingError(
            422, "Appointments must start on a 30-minute boundary."
        )

    doctor = get_doctor_or_raise(db, doctor_id)

    # Convert to Nairobi local time for the doctor's weekly schedule.
    from datetime import timezone as tz

    nairobi_time = start_at.astimezone(tz(timedelta(hours=3)))
    weekday = nairobi_time.weekday()
    local_start = nairobi_time.time().replace(tzinfo=None)
    local_end = (
        nairobi_time + timedelta(minutes=SLOT_MINUTES)
    ).time().replace(tzinfo=None)

    working_hours = db.scalars(
        select(DoctorWorkingHours).where(
            DoctorWorkingHours.doctor_id == doctor_id,
            DoctorWorkingHours.day_of_week == weekday,
        )
    ).all()

    within_working_hours = any(
        hours.start_time <= local_start
        and local_end <= hours.end_time
        for hours in working_hours
    )

    if not within_working_hours:
        raise BookingError(
            422, "The selected slot is outside the doctor's working hours."
        )

    # A booking is unique per doctor and start time.
    conflict_query = select(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.start_at == start_at,
        Appointment.status == "booked",
    )

    if exclude_appointment_id is not None:
        conflict_query = conflict_query.where(
            Appointment.id != exclude_appointment_id
        )

    if db.scalar(conflict_query) is not None:
        raise BookingError(409, "This appointment slot is already booked.")


def create_appointment(
    db: Session,
    doctor_id: int,
    patient_id: int,
    start_at: datetime,
) -> Appointment:
    validate_slot(db, doctor_id, start_at)

    patient = db.get(Patient, patient_id)
    if patient is None:
        raise BookingError(404, "Patient not found.")

    appointment = Appointment(
        doctor_id=doctor_id,
        patient_id=patient_id,
        start_at=start_at.astimezone(timezone.utc),
        status="booked",
    )

    db.add(appointment)

    try:
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception as exc:
        db.rollback()

        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            raise BookingError(
                409, "This appointment slot is already booked."
            ) from exc

        raise


def cancel_appointment(
    db: Session,
    appointment_id: int,
    reason: str,
) -> Appointment:
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise BookingError(404, "Appointment not found.")

    if appointment.status == "cancelled":
        raise BookingError(409, "Appointment is already cancelled.")

    appointment.status = "cancelled"
    appointment.cancellation_reason = reason
    appointment.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception:
        db.rollback()
        raise


def reschedule_appointment(
    db: Session,
    appointment_id: int,
    new_start_at: datetime,
) -> Appointment:
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise BookingError(404, "Appointment not found.")

    if appointment.status == "cancelled":
        raise BookingError(
            409, "Cancelled appointments cannot be rescheduled."
        )

    validate_slot(
        db=db,
        doctor_id=appointment.doctor_id,
        start_at=new_start_at,
        exclude_appointment_id=appointment.id,
    )

    appointment.start_at = new_start_at.astimezone(timezone.utc)
    appointment.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(appointment)
        return appointment
    except Exception as exc:
        db.rollback()

        from sqlalchemy.exc import IntegrityError

        if isinstance(exc, IntegrityError):
            raise BookingError(
                409, "This appointment slot is already booked."
            ) from exc

        raise
