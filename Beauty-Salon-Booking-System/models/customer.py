from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    phone: str = Field(min_length=5, max_length=40)


class CustomerCreate(CustomerBase):
    password: str = Field(min_length=6, max_length=120)


class CustomerUpdate(CustomerBase):
    password: str | None = Field(default=None, min_length=6, max_length=120)


class Customer(CustomerBase):
    id: int
    created_at: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    message: str
    user: Customer
