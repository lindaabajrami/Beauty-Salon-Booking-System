from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_api_key
from database import get_db_connection, row_to_dict, rows_to_dicts
from models.admin import AdminUser, AdminUserCreate, DashboardSummary


router = APIRouter()


def hash_admin_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary() -> dict:
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM customers) AS customers,
            (SELECT COUNT(*) FROM services) AS services,
            (SELECT COUNT(*) FROM staff) AS staff,
            (SELECT COUNT(*) FROM appointments) AS appointments,
            (
                SELECT COUNT(*) FROM appointments
                WHERE status = 'scheduled' AND appointment_date >= DATE('now')
            ) AS upcoming_appointments,
            (
                SELECT COUNT(*) FROM appointments
                WHERE status = 'completed'
            ) AS completed_appointments,
            (
                SELECT COALESCE(SUM(services.price), 0)
                FROM appointments
                JOIN services ON services.id = appointments.service_id
                WHERE appointments.status = 'completed'
            ) AS estimated_revenue
        """
    ).fetchone()
    conn.close()
    return dict(row)


@router.get("/settings")
def admin_settings(_: str = Depends(get_api_key)) -> dict:
    return {
        "api_key_header": "api-key",
        "write_routes_require_api_key": True,
    }


@router.get("/users", response_model=list[AdminUser])
def list_admin_users(_: str = Depends(get_api_key)) -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, username, email, role, active, created_at FROM admins ORDER BY username"
    ).fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.post("/users", response_model=AdminUser)
def create_admin_user(user: AdminUserCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    now = datetime.now().isoformat(timespec="seconds")
    try:
        cursor = conn.execute(
            """
            INSERT INTO admins (username, email, password_hash, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.username,
                user.email,
                hash_admin_password(user.password),
                user.role,
                int(user.active),
                now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, username, email, role, active, created_at FROM admins WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin username or email already exists.",
        ) from exc
    finally:
        conn.close()


@router.put("/users/{user_id}", response_model=AdminUser)
def update_admin_user(user_id: int, user: AdminUserCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE admins
            SET username = ?, email = ?, password_hash = ?, role = ?, active = ?
            WHERE id = ?
            """,
            (
                user.username,
                user.email,
                hash_admin_password(user.password),
                user.role,
                int(user.active),
                user_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Admin user not found")
        conn.commit()
        row = conn.execute(
            "SELECT id, username, email, role, active, created_at FROM admins WHERE id = ?",
            (user_id,),
        ).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin username or email already exists.",
        ) from exc
    finally:
        conn.close()


@router.delete("/users/{user_id}", response_model=dict)
def delete_admin_user(user_id: int, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    active_admins = conn.execute("SELECT COUNT(*) FROM admins WHERE active = 1").fetchone()[0]
    target = conn.execute("SELECT active FROM admins WHERE id = ?", (user_id,)).fetchone()
    if target is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Admin user not found")
    if active_admins <= 1 and target["active"]:
        conn.close()
        raise HTTPException(status_code=409, detail="At least one active admin must remain.")

    conn.execute("DELETE FROM admins WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"detail": "Admin user deleted"}
