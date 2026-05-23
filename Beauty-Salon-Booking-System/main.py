from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import API_PREFIX, API_VERSION, APP_NAME
from database import create_database
from routers import admin, api_key, appointments, auth, customers, services, staff


app = FastAPI(
    title=APP_NAME,
    description="FastAPI backend for a full-stack beauty salon booking system.",
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Auth"])
app.include_router(api_key.router, prefix=f"{API_PREFIX}/validate_key", tags=["API Key"])
app.include_router(admin.router, prefix=f"{API_PREFIX}/admin", tags=["Admin"])
app.include_router(customers.router, prefix=f"{API_PREFIX}/customers", tags=["Customers"])
app.include_router(services.router, prefix=f"{API_PREFIX}/services", tags=["Services"])
app.include_router(staff.router, prefix=f"{API_PREFIX}/staff", tags=["Staff"])
app.include_router(appointments.router, prefix=f"{API_PREFIX}/appointments", tags=["Appointments"])


@app.on_event("startup")
def startup() -> None:
    create_database()


@app.get("/")
def home() -> dict:
    return {
        "message": "Beauty Salon Booking System",
        "docs": "/docs",
        "api_prefix": API_PREFIX,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
