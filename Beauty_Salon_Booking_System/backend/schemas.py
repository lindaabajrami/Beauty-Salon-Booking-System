from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class ServiceCreate(BaseModel):
    service_name: str
    price: int


class AppointmentCreate(BaseModel):
    customer_name: str
    service_name: str
    date: str