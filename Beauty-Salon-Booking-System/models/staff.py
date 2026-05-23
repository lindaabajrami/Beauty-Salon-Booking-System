from __future__ import annotations

from pydantic import BaseModel, Field


class StaffBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=160)
    phone: str = Field(min_length=5, max_length=40)
    active: bool = True


class StaffCreate(StaffBase):
    pass


class Staff(StaffBase):
    id: int
