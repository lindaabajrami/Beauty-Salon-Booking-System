from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from auth.security import hash_password, verify_password
from database import get_db_connection, row_to_dict
from models.customer import CustomerCreate, CustomerUpdate, LoginRequest, LoginResponse


router = APIRouter()


@router.post("/signup", response_model=LoginResponse)
def signup(customer: CustomerCreate) -> dict:
    conn = get_db_connection()
    now = datetime.now().isoformat(timespec="seconds")
    try:
        cursor = conn.execute(
            """
            INSERT INTO customers (full_name, email, phone, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                customer.full_name,
                customer.email,
                customer.phone,
                hash_password(customer.password),
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, full_name, email, phone, created_at FROM customers WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return {"message": "Signup successful", "user": row_to_dict(row)}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc
    finally:
        conn.close()


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest) -> dict:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM customers WHERE email = ?",
        (credentials.email,),
    ).fetchone()
    conn.close()

    if row is None or not verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = {
        "id": row["id"],
        "full_name": row["full_name"],
        "email": row["email"],
        "phone": row["phone"],
        "created_at": row["created_at"],
    }
    return {"message": "Login successful", "user": user}


@router.put("/profile/{customer_id}", response_model=LoginResponse)
def update_profile(customer_id: int, customer: CustomerUpdate) -> dict:
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    password_hash = existing["password_hash"]
    if customer.password:
        password_hash = hash_password(customer.password)

    try:
        conn.execute(
            """
            UPDATE customers
            SET full_name = ?, email = ?, phone = ?, password_hash = ?
            WHERE id = ?
            """,
            (customer.full_name, customer.email, customer.phone, password_hash, customer_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, full_name, email, phone, created_at FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
        return {"message": "Profile updated", "user": row_to_dict(row)}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="A user with this email already exists.") from exc
    finally:
        conn.close()
