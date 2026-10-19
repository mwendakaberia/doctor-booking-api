
import os
from datetime import date, timedelta, time

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.db.dependencies import get_db
from app.main import app
from app.models import Doctor, DoctorWorkingHours, Patient


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing from .env")

if not TEST_DATABASE_URL.endswith("/doctor_booking_test"):
    raise RuntimeError(
        "Tests must use the doctor_booking_test database."
    )

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_data(db_session):
    doctor = Doctor(
        full_name="Dr. Test Doctor",
        specialization="General Practice",
        is_active=True,
    )

    patient = Patient(
        full_name="Test Patient",
        email="patient@test.example",
    )

    db_session.add_all([doctor, patient])
    db_session.flush()

    target_date = date.today() + timedelta(days=1)

    working_hours = DoctorWorkingHours(
        doctor_id=doctor.id,
        day_of_week=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(12, 0),
    )

    db_session.add(working_hours)
    db_session.commit()

    return {
        "doctor_id": doctor.id,
        "patient_id": patient.id,
        "date": target_date.isoformat(),
        "slot": f"{target_date.isoformat()}T09:00:00+03:00",
        "second_slot": f"{target_date.isoformat()}T10:00:00+03:00",
    }
