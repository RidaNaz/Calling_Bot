from fastapi import APIRouter
from .routes import twillio_incoming_calls
from .routes import health_check
from .routes import appointments

api_router = APIRouter()
api_router.include_router(
    health_check.router, prefix="/health_check", tags=["health_check"]
)

api_router.include_router(
    twillio_incoming_calls.router, prefix="/voice", tags=["incoming_calls"]
)

api_router.include_router(
    appointments.router, prefix="/appointments", tags=["appointments"]
)