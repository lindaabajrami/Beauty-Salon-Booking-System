from fastapi import FastAPI
from routers import users, services, appointments

app = FastAPI()

app.include_router(users.router)
app.include_router(services.router)
app.include_router(appointments.router)

@app.get("/")
def home():
    return {"message": "Beauty Salon Booking System"}