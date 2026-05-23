from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_api_key
from database import get_db_connection, row_to_dict, rows_to_dicts
from models.appointment import AppointmentCreate, AppointmentDetail


router = APIRouter()

APPOINTMENT_DETAIL_QUERY = """
    SELECT
        appointments.*,
        customers.full_name AS customer_name,
        services.name AS service_name,
        services.category AS service_category,
        services.price,
        services.duration_minutes,
        staff.full_name AS staff_name
    FROM appointments
    JOIN customers ON customers.id = appointments.customer_id
    JOIN services ON services.id = appointments.service_id
    JOIN staff ON staff.id = appointments.staff_id
"""


def appointment_detail_or_404(appointment_id: int) -> dict:
    conn = get_db_connection()
    row = conn.execute(
        f"{APPOINTMENT_DETAIL_QUERY} WHERE appointments.id = ?",
        (appointment_id,),
    ).fetchone()
    conn.close()
    appointment = row_to_dict(row)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


def ensure_foreign_keys_exist(conn, appointment: AppointmentCreate) -> None:
    checks = [
        ("customers", appointment.customer_id, "Customer"),
        ("services", appointment.service_id, "Service"),
        ("staff", appointment.staff_id, "Staff member"),
    ]
    for table, entity_id, label in checks:
        exists = conn.execute(f"SELECT id FROM {table} WHERE id = ?", (entity_id,)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail=f"{label} not found")


@router.get("/", response_model=list[AppointmentDetail])
def list_appointments(status_filter: str | None = None) -> list[dict]:
    conn = get_db_connection()
    if status_filter:
        rows = conn.execute(
            f"{APPOINTMENT_DETAIL_QUERY} WHERE appointments.status = ? "
            "ORDER BY appointments.appointment_date, appointments.appointment_time",
            (status_filter,),
        ).fetchall()
    else:
        rows = conn.execute(
            f"{APPOINTMENT_DETAIL_QUERY} "
            "ORDER BY appointments.appointment_date, appointments.appointment_time"
        ).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/{appointment_id}", response_model=AppointmentDetail)
def get_appointment(appointment_id: int) -> dict:
    return appointment_detail_or_404(appointment_id)


@router.post("/", response_model=AppointmentDetail)
def create_appointment(appointment: AppointmentCreate) -> dict:
    conn = get_db_connection()
    ensure_foreign_keys_exist(conn, appointment)
    now = datetime.now().isoformat(timespec="seconds")
    try:
        cursor = conn.execute(
            """
            INSERT INTO appointments (
                customer_id, service_id, staff_id, appointment_date,
                appointment_time, status, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                appointment.customer_id,
                appointment.service_id,
                appointment.staff_id,
                appointment.appointment_date,
                appointment.appointment_time,
                appointment.status,
                appointment.notes,
                now,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment conflict.") from exc
    finally:
        conn.close()

    return appointment_detail_or_404(new_id)


@router.put("/{appointment_id}", response_model=AppointmentDetail)
def update_appointment(
    appointment_id: int,
    appointment: AppointmentCreate,
    _: str = Depends(get_api_key),
) -> dict:
    conn = get_db_connection()
    ensure_foreign_keys_exist(conn, appointment)
    cursor = conn.execute(
        """
        UPDATE appointments
        SET customer_id = ?, service_id = ?, staff_id = ?, appointment_date = ?,
            appointment_time = ?, status = ?, notes = ?
        WHERE id = ?
        """,
        (
            appointment.customer_id,
            appointment.service_id,
            appointment.staff_id,
            appointment.appointment_date,
            appointment.appointment_time,
            appointment.status,
            appointment.notes,
            appointment_id,
        ),
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")
    conn.commit()
    conn.close()
    return appointment_detail_or_404(appointment_id)


@router.delete("/{appointment_id}", response_model=dict)
def delete_appointment(appointment_id: int, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")
    conn.commit()
    conn.close()
    return {"detail": "Appointment deleted"}
