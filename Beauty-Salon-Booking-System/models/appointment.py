from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AppointmentStatus = Literal["scheduled", "completed", "cancelled", "no_show"]


class AppointmentBase(BaseModel):
    customer_id: int = Field(gt=0)
    service_id: int = Field(gt=0)
    staff_id: int = Field(gt=0)
    appointment_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    appointment_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    status: AppointmentStatus = "scheduled"
    notes: str = ""


class AppointmentCreate(AppointmentBase):
    pass


class Appointment(AppointmentBase):
    id: int
    created_at: str


class AppointmentDetail(Appointment):
    customer_name: str
    service_name: str
    staff_name: str
    service_category: str
    price: float
    duration_minutes: int
