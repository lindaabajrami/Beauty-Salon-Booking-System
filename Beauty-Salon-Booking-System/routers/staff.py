from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_api_key
from database import get_db_connection, row_to_dict, rows_to_dicts
from models.staff import Staff, StaffCreate


router = APIRouter()


@router.get("/", response_model=list[Staff])
def list_staff(active_only: bool = False) -> list[dict]:
    conn = get_db_connection()
    if active_only:
        rows = conn.execute("SELECT * FROM staff WHERE active = 1 ORDER BY full_name").fetchall()
    else:
        rows = conn.execute("SELECT * FROM staff ORDER BY full_name").fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/{staff_id}", response_model=Staff)
def get_staff_member(staff_id: int) -> dict:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
    conn.close()
    staff_member = row_to_dict(row)
    if staff_member is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff_member


@router.post("/", response_model=Staff)
def create_staff_member(staff_member: StaffCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO staff (full_name, specialty, email, phone, active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                staff_member.full_name,
                staff_member.specialty,
                staff_member.email,
                staff_member.phone,
                int(staff_member.active),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM staff WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Staff email '{staff_member.email}' already exists.",
        ) from exc
    finally:
        conn.close()


@router.put("/{staff_id}", response_model=Staff)
def update_staff_member(staff_id: int, staff_member: StaffCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE staff
            SET full_name = ?, specialty = ?, email = ?, phone = ?, active = ?
            WHERE id = ?
            """,
            (
                staff_member.full_name,
                staff_member.specialty,
                staff_member.email,
                staff_member.phone,
                int(staff_member.active),
                staff_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Staff member not found")
        conn.commit()
        row = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Staff email '{staff_member.email}' already exists.",
        ) from exc
    finally:
        conn.close()


@router.delete("/{staff_id}", response_model=dict)
def delete_staff_member(staff_id: int, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Staff member not found")
        conn.commit()
        return {"detail": "Staff member deleted"}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Staff member is used by appointments and cannot be deleted.",
        ) from exc
    finally:
        conn.close()
