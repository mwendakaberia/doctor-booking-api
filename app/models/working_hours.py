
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class DoctorWorkingHours(Base):
    __tablename__ = "doctor_working_hours"

    __table_args__ = (
        CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="ck_working_hours_day",
        ),
        CheckConstraint(
            "start_time < end_time",
            name="ck_working_hours_valid_time",
        ),
        UniqueConstraint(
            "doctor_id",
            "day_of_week",
            "start_time",
            name="uq_doctor_working_hours_start",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    start_time: Mapped[object] = mapped_column(
        Time, nullable=False
    )
    end_time: Mapped[object] = mapped_column(
        Time, nullable=False
    )

    doctor: Mapped["Doctor"] = relationship(
        back_populates="working_hours"
    )
