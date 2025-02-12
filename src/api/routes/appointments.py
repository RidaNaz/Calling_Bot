from fastapi import APIRouter, HTTPException
from datetime import datetime
from pydantic import BaseModel
from datetime import datetime

class Appointment(BaseModel):
    client_name: str
    email : str
    phone_number: str
    appointment_date: datetime

router = APIRouter()
appointments = []  # Temporary in-memory storage

@router.post("/schedule")
async def schedule_appointment(appointment: Appointment):
    if appointment.appointment_date < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot schedule for past dates.")
    
    appointments.append(appointment)
    return {"message": "Appointment scheduled successfully", "appointment": appointment}

@router.get("/list")
async def list_appointments():
    return appointments