from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_api_key, hash_password
from database import get_db_connection, row_to_dict, rows_to_dicts
from models.customer import Customer, CustomerCreate, CustomerUpdate


router = APIRouter()


CUSTOMER_SELECT = "SELECT id, full_name, email, phone, created_at FROM customers"


@router.get("/", response_model=list[Customer])
def list_customers() -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(f"{CUSTOMER_SELECT} ORDER BY full_name").fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: int) -> dict:
    conn = get_db_connection()
    row = conn.execute(f"{CUSTOMER_SELECT} WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    customer = row_to_dict(row)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/", response_model=Customer)
def create_customer(customer: CustomerCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    now = datetime.now().isoformat(timespec="seconds")
    try:
        cursor = conn.execute(
            """
            INSERT INTO customers (full_name, email, phone, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (customer.full_name, customer.email, customer.phone, hash_password(customer.password), now),
        )
        conn.commit()
        row = conn.execute(f"{CUSTOMER_SELECT} WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer email already exists.") from exc
    finally:
        conn.close()


@router.put("/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: CustomerUpdate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if existing is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    password_hash = hash_password(customer.password) if customer.password else existing["password_hash"]
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
        row = conn.execute(f"{CUSTOMER_SELECT} WHERE id = ?", (customer_id,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Customer email already exists.") from exc
    finally:
        conn.close()


@router.delete("/{customer_id}", response_model=dict)
def delete_customer(customer_id: int, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")
    conn.commit()
    conn.close()
    return {"detail": "Customer and related appointments deleted"}
