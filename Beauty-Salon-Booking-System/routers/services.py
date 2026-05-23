from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import get_api_key
from database import get_db_connection, row_to_dict, rows_to_dicts
from models.service import Service, ServiceCreate


router = APIRouter()


@router.get("/", response_model=list[Service])
def list_services(active_only: bool = False) -> list[dict]:
    conn = get_db_connection()
    if active_only:
        rows = conn.execute("SELECT * FROM services WHERE active = 1 ORDER BY category, name").fetchall()
    else:
        rows = conn.execute("SELECT * FROM services ORDER BY category, name").fetchall()
    conn.close()
    return rows_to_dicts(rows)


@router.get("/{service_id}", response_model=Service)
def get_service(service_id: int) -> dict:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    conn.close()
    service = row_to_dict(row)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.post("/", response_model=Service)
def create_service(service: ServiceCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO services (name, category, duration_minutes, price, active, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                service.name,
                service.category,
                service.duration_minutes,
                service.price,
                int(service.active),
                service.image_path,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM services WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service '{service.name}' already exists.",
        ) from exc
    finally:
        conn.close()


@router.put("/{service_id}", response_model=Service)
def update_service(service_id: int, service: ServiceCreate, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE services
            SET name = ?, category = ?, duration_minutes = ?, price = ?, active = ?, image_path = ?
            WHERE id = ?
            """,
            (
                service.name,
                service.category,
                service.duration_minutes,
                service.price,
                int(service.active),
                service.image_path,
                service_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        conn.commit()
        row = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
        return row_to_dict(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Service '{service.name}' already exists.",
        ) from exc
    finally:
        conn.close()


@router.delete("/{service_id}", response_model=dict)
def delete_service(service_id: int, _: str = Depends(get_api_key)) -> dict:
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM services WHERE id = ?", (service_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Service not found")
        conn.commit()
        return {"detail": "Service deleted"}
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service is used by appointments and cannot be deleted.",
        ) from exc
    finally:
        conn.close()
