from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse

from app.routes.appointments import router as appointments_router
from app.routes.availability import router as availability_router
from app.routes.patients import router as patients_router
from app.services.appointment_service import BookingError

app = FastAPI(
    title="Doctor Booking API",
    description="An API for managing doctor appointments",
    version="1.0.0",
)

@app.exception_handler(BookingError)
async def booking_error_handler(request: Request, exc: BookingError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(appointments_router)
app.include_router(availability_router)
app.include_router(patients_router)


@app.get("/")
def root():
    return {
        "message": "Doctor Booking API is running",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
