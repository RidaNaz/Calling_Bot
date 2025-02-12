#!/usr/bin/env python
import os
from dotenv import load_dotenv
from twilio.rest import Client

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.main import api_router

load_dotenv()

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)


TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN= os.getenv("TWILIO_AUTH_TOKEN")
auth_token = os.environ["TWILIO_AUTH_TOKEN"]

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

async def log_operation(task_id: int):
    # Placeholder function to simulate an async background task
    print(f"Logging operation for item_id: {task_id}")