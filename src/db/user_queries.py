from __future__ import annotations

from typing import Optional

from src.db.connection import get_db_conn


def check_user_exists(employee_id: str, email: str) -> bool:
    """Return True if either employee_id or email already exists."""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1
            FROM users
            WHERE employee_id = %s OR email = %s
            LIMIT 1
            """,
            (employee_id, email),
        )
        exists = cur.fetchone() is not None
        cur.close()
    return exists


def create_user(
    *,
    employee_id: str,
    name: str,
    email: str,
    password_hash: str,
    grade: Optional[str] = None,
    role: str = "employee",
    department: Optional[str] = None,
    designation: Optional[str] = None,
    manager_id: Optional[str] = None,
    city: Optional[str] = None,
    gender: Optional[str] = None,
) -> dict:
    """Insert a new user record and return the persisted info."""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (
                employee_id,
                name,
                email,
                password_hash,
                grade,
                role,
                department,
                designation,
                manager_id,
                city,
                gender,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING employee_id, name, email, role, grade
            """,
            (
                employee_id,
                name,
                email,
                password_hash,
                grade,
                role,
                department,
                designation,
                manager_id,
                city,
                gender,
            ),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()

    return {
        "employee_id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3],
        "grade": row[4],
    }
