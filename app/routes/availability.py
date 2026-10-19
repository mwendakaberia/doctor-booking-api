
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models import Appointment, Doctor, DoctorWorkingHours
from app.services.appointment_service import get_doctor_or_raise


router = APIRouter(tags=["Availability"])


@router.get("/doctors/{doctor_id}/availability")
def doctor_availability(
    doctor_id: int,
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
):
    doctor = get_doctor_or_raise(db, doctor_id)

    weekday = date_value.weekday()

    schedules = db.scalars(
        select(DoctorWorkingHours).where(
            DoctorWorkingHours.doctor_id == doctor_id,
            DoctorWorkingHours.day_of_week == weekday,
        ).order_by(DoctorWorkingHours.start_time)
    ).all()

    if not schedules:
        return {
            "doctor_id": doctor_id,
            "date": date_value.isoformat(),
            "available_slots": [],
        }

    booked = db.scalars(
        select(Appointment.start_at).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "booked",
            Appointment.start_at >= datetime.combine(
                date_value, time.min, tzinfo=timezone(timedelta(hours=3))
            ).astimezone(timezone.utc),
            Appointment.start_at < datetime.combine(
                date_value + timedelta(days=1),
                time.min,
                tzinfo=timezone(timedelta(hours=3)),
            ).astimezone(timezone.utc),
        )
    ).all()

    booked_times = set(booked)
    now = datetime.now(timezone.utc)
    available_slots = []

    for schedule in schedules:
        slot_start = datetime.combine(
            date_value,
            schedule.start_time,
            tzinfo=timezone(timedelta(hours=3)),
        )

        end_time = datetime.combine(
            date_value,
            schedule.end_time,
            tzinfo=timezone(timedelta(hours=3)),
        )

        while slot_start + timedelta(minutes=30) <= end_time:
            slot_utc = slot_start.astimezone(timezone.utc)

            if (
                slot_utc > now + timedelta(hours=1)
                and slot_utc not in booked_times
            ):
                available_slots.append(slot_utc.isoformat())

            slot_start += timedelta(minutes=30)

    return {
        "doctor_id": doctor_id,
        "date": date_value.isoformat(),
        "available_slots": available_slots,
    }
