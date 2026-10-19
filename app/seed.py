
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Doctor, DoctorWorkingHours, Patient


def seed_database():
    db = SessionLocal()

    try:
        doctor = db.scalar(
            select(Doctor).where(
                Doctor.full_name == "Dr. Mwenda Kaberia"
            )
        )

        if doctor is None:
            doctor = Doctor(
                full_name="Dr. Mwenda Kaberia",
                specialization="Neurologist",
                is_active=True,
            )
            db.add(doctor)
            db.flush()

        patient = db.scalar(
            select(Patient).where(
                Patient.email == "test.patient@gmail.com"
            )
        )

        if patient is None:
            patient = Patient(
                full_name="Test Patient",
                email="test.patient@gmail.com",
            )
            db.add(patient)
            db.flush()

        target_date = date.today() + timedelta(days=1)
        weekday = target_date.weekday()

        schedule = db.scalar(
            select(DoctorWorkingHours).where(
                DoctorWorkingHours.doctor_id == doctor.id,
                DoctorWorkingHours.day_of_week == weekday,
                DoctorWorkingHours.start_time == time(9, 0),
            )
        )

        if schedule is None:
            schedule = DoctorWorkingHours(
                doctor_id=doctor.id,
                day_of_week=weekday,
                start_time=time(9, 0),
                end_time=time(15, 0),
            )
            db.add(schedule)

        db.commit()

        print("Sample data is ready!")
        print(f"Doctor ID: {doctor.id}")
        print(f"Patient ID: {patient.id}")
        print(f"Test date: {target_date.isoformat()}")
        print("Working hours: 09:00–15:00 Nairobi time")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
