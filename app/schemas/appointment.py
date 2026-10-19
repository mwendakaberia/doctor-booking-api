
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppointmentCreate(BaseModel):
    doctor_id: int = Field(gt=0)
    patient_id: int = Field(gt=0)
    start_at: datetime

    @field_validator("start_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "start_at must include a timezone, e.g. +03:00 or Z"
            )
        return value.astimezone(timezone.utc)


class AppointmentReschedule(BaseModel):
    start_at: datetime

    @field_validator("start_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "start_at must include a timezone, e.g. +03:00 or Z"
            )
        return value.astimezone(timezone.utc)


class AppointmentCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    start_at: datetime
    status: str
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
