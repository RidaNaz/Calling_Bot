from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from ...utils.google_calendar import create_appointment

router = APIRouter()

@router.post("/schedule")
async def schedule_appointment(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    appointment_time = data.get("appointment_time")  # Format: "2025-02-09T15:00:00"

    start_time = datetime.fromisoformat(appointment_time)
    end_time = start_time + timedelta(minutes=30)  # 30-minute appointment

    link = create_appointment(
        summary=f"Appointment with {name}",
        description="Virtual Consultation",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        attendees_emails=[email]
    )

    return {"message": "Appointment scheduled successfully!", "link": link}