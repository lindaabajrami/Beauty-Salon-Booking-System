from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    duration_minutes: int = Field(ge=5, le=480)
    price: float = Field(ge=0)
    active: bool = True
    image_path: str = ""


class ServiceCreate(ServiceBase):
    pass


class Service(ServiceBase):
    id: int
