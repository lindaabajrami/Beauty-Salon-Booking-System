from __future__ import annotations

from pydantic import BaseModel, Field


class AdminUserBase(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(min_length=5, max_length=160)
    role: str = Field(default="admin", min_length=3, max_length=40)
    active: bool = True


class AdminUserCreate(AdminUserBase):
    password: str = Field(min_length=6, max_length=120)


class AdminUser(AdminUserBase):
    id: int
    created_at: str


class DashboardSummary(BaseModel):
    customers: int
    services: int
    staff: int
    appointments: int
    upcoming_appointments: int
    completed_appointments: int
    estimated_revenue: float
