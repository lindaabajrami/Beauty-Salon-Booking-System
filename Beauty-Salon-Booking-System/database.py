from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Iterable

from auth.security import hash_password
from config import (
    DATABASE_DIR,
    DATABASE_PATH,
    SEEDED_ADMIN_PASSWORD,
    SEEDED_ADMIN_USERNAME,
    SEEDED_USER_PASSWORD,
)


def get_db_connection() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def table_is_empty(conn: sqlite3.Connection, table_name: str) -> bool:
    return conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0] == 0


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(column["name"] == column_name for column in columns)


def add_column_if_missing(conn: sqlite3.Connection, table_name: str, column_sql: str) -> None:
    column_name = column_sql.split()[0]
    if not column_exists(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


def create_database() -> None:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            price REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            image_path TEXT NOT NULL DEFAULT ''
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE RESTRICT,
            FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE RESTRICT
        )
        """
    )

    add_column_if_missing(conn, "customers", "password_hash TEXT NOT NULL DEFAULT ''")
    add_column_if_missing(conn, "services", "image_path TEXT NOT NULL DEFAULT ''")

    conn.commit()
    seed_database(conn)
    conn.close()


def seed_database(conn: sqlite3.Connection) -> None:
    now = datetime.now().isoformat(timespec="seconds")

    if table_is_empty(conn, "admins"):
        conn.execute(
            """
            INSERT INTO admins (username, email, password_hash, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                SEEDED_ADMIN_USERNAME,
                "admin@bloombeauty.local",
                hash_password(SEEDED_ADMIN_PASSWORD),
                "owner",
                1,
                now,
            ),
        )

    if table_is_empty(conn, "customers"):
        conn.executemany(
            """
            INSERT INTO customers (full_name, email, phone, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Mira Novak", "mira@example.com", "+36 20 111 2233", hash_password(SEEDED_USER_PASSWORD), now),
                ("Lina Kovacs", "lina@example.com", "+36 30 222 3344", hash_password("lina123"), now),
                ("Sara Varga", "sara@example.com", "+36 70 333 4455", hash_password("sara123"), now),
                ("Emma Horvath", "emma@example.com", "+36 20 444 5566", hash_password("emma123"), now),
            ],
        )
    else:
        conn.execute(
            "UPDATE customers SET password_hash = ? WHERE email = ? AND password_hash = ''",
            (hash_password(SEEDED_USER_PASSWORD), "mira@example.com"),
        )

    if table_is_empty(conn, "services"):
        conn.executemany(
            """
            INSERT INTO services (name, category, duration_minutes, price, active, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("Signature Facial", "Skin Care", 60, 85.0, 1, "assets/services/signature_facial.png"),
                ("Gel Manicure", "Nails", 45, 38.0, 1, "assets/services/gel_manicure.png"),
                ("Balayage Refresh", "Hair", 120, 145.0, 1, "assets/services/balayage_refresh.png"),
                ("Brow Shape and Tint", "Brows", 30, 32.0, 1, "assets/services/brow_shape_tint.png"),
                ("Relaxing Massage", "Wellness", 75, 95.0, 1, "assets/services/relaxing_massage.png"),
            ],
        )
    else:
        image_updates = [
            ("assets/services/signature_facial.png", "Signature Facial"),
            ("assets/services/gel_manicure.png", "Gel Manicure"),
            ("assets/services/balayage_refresh.png", "Balayage Refresh"),
            ("assets/services/brow_shape_tint.png", "Brow Shape and Tint"),
            ("assets/services/relaxing_massage.png", "Relaxing Massage"),
        ]
        conn.executemany("UPDATE services SET image_path = ? WHERE name = ?", image_updates)

    if table_is_empty(conn, "staff"):
        conn.executemany(
            """
            INSERT INTO staff (full_name, specialty, email, phone, active)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("Nora Fekete", "Skin Care", "nora@bloombeauty.local", "+36 1 555 0101", 1),
                ("Anna Toth", "Nails", "anna@bloombeauty.local", "+36 1 555 0102", 1),
                ("Kata Balazs", "Hair", "kata@bloombeauty.local", "+36 1 555 0103", 1),
                ("Reka Molnar", "Brows", "reka@bloombeauty.local", "+36 1 555 0104", 1),
            ],
        )

    if table_is_empty(conn, "appointments"):
        base = date.today()
        conn.executemany(
            """
            INSERT INTO appointments (
                customer_id, service_id, staff_id, appointment_date,
                appointment_time, status, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (1, 1, 1, (base - timedelta(days=5)).isoformat(), "10:00", "completed", "First visit", now),
                (2, 2, 2, (base - timedelta(days=2)).isoformat(), "13:30", "completed", "", now),
                (3, 3, 3, (base + timedelta(days=1)).isoformat(), "09:00", "scheduled", "Prefers warm toner", now),
                (4, 4, 4, (base + timedelta(days=3)).isoformat(), "16:00", "scheduled", "", now),
                (1, 5, 1, (base + timedelta(days=7)).isoformat(), "11:30", "scheduled", "Birthday booking", now),
            ],
        )

    conn.commit()


if __name__ == "__main__":
    create_database()
