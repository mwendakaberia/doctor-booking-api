
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentResponse,
)
from app.services.appointment_service import (
    cancel_appointment,
    create_appointment,
    reschedule_appointment,
)


router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentResponse, status_code=201)
def book_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
):
    return create_appointment(
        db=db,
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        start_at=payload.start_at,
    )


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment_endpoint(
    appointment_id: int,
    payload: AppointmentCancel,
    db: Session = Depends(get_db),
):
    return cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        reason=payload.reason,
    )


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment_endpoint(
    appointment_id: int,
    payload: AppointmentReschedule,
    db: Session = Depends(get_db),
):
    return reschedule_appointment(
        db=db,
        appointment_id=appointment_id,
        new_start_at=payload.start_at,
    )
