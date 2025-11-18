# src/db/travel_queries.py
from src.db.connection import get_db_conn
import uuid, datetime
 
_DUPLICATE_SAFE_STATUSES = {
    "draft",
    "rejected",
    "rejected_manager",
    "rejected_hr",
    "declined",
    "cancelled",
}
 
_MANAGER_APPROVED_STATUSES = {
    "accepted_manager",
    "accpeted_manager",
    "manager_approved",
}
 
_HR_ACTION_STATUSES = {
    "hr_approved",
    "completed_hr",
    "booked",
}
 
_HR_ELIGIBLE_STATUSES = _MANAGER_APPROVED_STATUSES | _HR_ACTION_STATUSES
 
 
def _inject_status_fields(rows):
    """Ensure each travel indent dict exposes status/status_code even if column missing."""
    normalized = []
    for row in rows:
        status_value = (row.get("status") or row.get("is_approved") or "pending").strip().lower()
        row = dict(row)
        row.setdefault("status", status_value)
        row.setdefault("status_code", status_value)
        normalized.append(row)
    return normalized
 
 
def _normalize_place(value):
    return (value or "").strip().lower()
 
 
def _ensure_no_duplicate_active(cur, employee_id, from_city, to_city, start_date, end_date, exclude_indent_id=None):
    """Prevent raising the same trip twice for the same employee."""
 
    # only enforce dedupe for confirmed submissions
    from_key = _normalize_place(from_city)
    to_key = _normalize_place(to_city)
 
    cur.execute(
        """
        SELECT indent_id, COALESCE(is_approved, 'pending') AS status_code
        FROM travel_indents
        WHERE employee_id = %s
          AND LOWER(TRIM(COALESCE(from_city,''))) = %s
          AND LOWER(TRIM(COALESCE(to_city,''))) = %s
          AND travel_start_date = %s
          AND travel_end_date = %s
          AND (%s IS NULL OR indent_id <> %s)
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (employee_id, from_key, to_key, start_date, end_date, exclude_indent_id, exclude_indent_id),
    )
    row = cur.fetchone()
    if not row:
        return
 
    _, status_code = row
    normalized_status = (status_code or "pending").strip().lower()
    if normalized_status in _DUPLICATE_SAFE_STATUSES:
        return
 
    raise ValueError(
        "You already have a request for the same route and dates. Please update the existing ticket instead of creating a duplicate."
    )
 
 
def _require_manager_approval_for_hr(cur, indent_id: str):
    cur.execute(
        "SELECT COALESCE(is_approved, 'pending') FROM travel_indents WHERE indent_id=%s",
        (indent_id,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError("Travel indent not found")
 
    status = (row[0] or "pending").strip().lower()
    if status not in _HR_ELIGIBLE_STATUSES:
        raise ValueError("Manager approval required before HR can approve or book this ticket.")
    return status
 
def get_user_by_employee_id(employee_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT employee_id, name, email, password_hash, grade, role, is_active, manager_id
            FROM users WHERE employee_id=%s
        """, (employee_id,))
        row = cur.fetchone()
        cur.close()
    if not row:
        return None
    return {
        "employee_id": row[0],
        "name": row[1],
        "email": row[2],
        "password_hash": row[3],
        "grade": row[4],
        "role": row[5],
        "is_active": row[6],
        "manager_id": row[7],
    }
 
def get_user_details(employee_id: str):
    u = get_user_by_employee_id(employee_id)
    if not u:
        return None
    return {k: u[k] for k in ("employee_id","name","email","grade","role","manager_id","is_active")}
 
def fetch_eligible_hotels(grade, city, limit=5):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, hotel_name, city, final_corporate_rate, grade_eligibility, is_active
            FROM tied_up_hotels
            WHERE city ILIKE %s AND is_active = TRUE
            ORDER BY final_corporate_rate ASC
            LIMIT %s
        """, (city, limit))
        rows = cur.fetchall()
        cur.close()
    hotels = []
    for r in rows:
        hotels.append({
            "id": r[0], "name": r[1], "city": r[2], "rate": float(r[3]), "grade_eligibility": r[4]
        })
    # filter by grade
    return [h for h in hotels if (h["grade_eligibility"] is None) or (grade in h["grade_eligibility"])]
 
def fetch_flights(source, destination, date=None):
    # Demo stub; replace with real API
    return [
        {"airline": "Indigo", "flight_no":"6E-502", "price":8200, "dep_time":"09:00"},
        {"airline": "Vistara", "flight_no":"UK-864", "price":9100, "dep_time":"13:00"}
    ]
 
def create_travel_indent(employee_id, intent, selected_flight, selected_hotel):
    indent_id = f"TIX{str(uuid.uuid4())[:8].upper()}"
    total_days = intent.get("total_days", 1)
    est_flight = selected_flight.get("price", 0)
    hotel_rate = selected_hotel.get("rate", 0)
    total_estimated = est_flight + hotel_rate * total_days
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO travel_indents
            (indent_id, employee_id, purpose, source_city, destination_city, start_date, end_date, total_days,
             estimated_flight_cost, preferred_hotel_id, status, manager_approval_status, budget_approval_status, hr_approval_status, total_estimated_cost, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())
        """, (
            indent_id, employee_id, intent.get("purpose"), intent.get("source_city"), intent.get("destination_city"),
            intent.get("start_date"), intent.get("end_date"), total_days, est_flight, selected_hotel.get("id"),
            "SUBMITTED", "PENDING", "PENDING", "PENDING", total_estimated
        ))
        conn.commit()
        cur.close()
    # insert workflow manager step
    user = get_user_by_employee_id(employee_id)
    manager_id = user.get("manager_id")
    if manager_id:
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO approval_workflow (indent_id, approver_id, approval_type, status, created_at)
                VALUES (%s,%s,%s,%s,NOW())
            """, (indent_id, manager_id, "MANAGER", "PENDING"))
            conn.commit()
            cur.close()
    return indent_id
 
def get_pending_manager_tickets(manager_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ti.indent_id, ti.employee_id, u.name, ti.purpose, ti.status, ti.total_estimated_cost
            FROM travel_indents ti
            JOIN users u ON ti.employee_id = u.employee_id
            WHERE u.manager_id = %s AND ti.manager_approval_status = 'PENDING'
        """, (manager_id,))
        rows = cur.fetchall()
        cur.close()
    return [dict(zip(["indent_id","employee_id","employee_name","purpose","status","total_estimated_cost"], r)) for r in rows]
 
def get_indent_details(indent_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT indent_id, employee_id, purpose, source_city, destination_city, start_date, end_date, total_days, total_estimated_cost, status
            FROM travel_indents WHERE indent_id=%s
        """, (indent_id,))
        row = cur.fetchone()
        cur.close()
    if not row:
        return None
    return dict(zip(["indent_id","employee_id","purpose","source_city","destination_city","start_date","end_date","total_days","total_estimated_cost","status"], row))
 
def fetch_manager_indents(manager_id):
    """Fetch all travel indents for employees reporting to this manager"""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ti.*,
                   u.name AS employee_name,
                   u.email,
                   u.grade,
                   u.department,
                   u.designation
            FROM travel_indents ti
            JOIN users u ON ti.employee_id = u.employee_id
            ORDER BY ti.created_at DESC
        """, (manager_id,))
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        cur.close()
    data = [dict(zip(cols, r)) for r in rows]
    return _inject_status_fields(data)
   
def fetch_manager_pending(manager_id):
    """Fetch only pending approval tickets"""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ti.*,
                   u.name AS employee_name,
                   u.email,
                   u.grade,
                   u.department,
                   u.designation
            FROM travel_indents ti
            JOIN users u ON ti.employee_id = u.employee_id
            WHERE ti.is_approved = 'pending'
            ORDER BY ti.created_at DESC
        """, (manager_id,))
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        cur.close()
    data = [dict(zip(cols, r)) for r in rows]
    return _inject_status_fields(data)
 
def fetch_manager_approved(manager_id):
    """Fetch approved tickets"""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ti.*,
                   u.name AS employee_name,
                   u.email,
                   u.grade,
                   u.department,
                   u.designation
            FROM travel_indents ti
            JOIN users u ON ti.employee_id = u.employee_id
            WHERE ti.is_approved = 'accepted_manager'
            ORDER BY ti.created_at DESC
        """, (manager_id,))
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        cur.close() # It's good practice to close the cursor explicitly
    data = [dict(zip(cols, r)) for r in rows]
    return _inject_status_fields(data)
   
def approve_indent_manager(indent_id):
    """Mark indent as manager approved"""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE travel_indents
            SET is_approved = 'accepted_manager',
                updated_at = CURRENT_TIMESTAMP
            WHERE indent_id = %s
        """, (indent_id,))
        conn.commit()
        return True
 
def fetch_employee_profile(employee_id):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT employee_id, name, email, grade, department,
                   designation, manager_id, created_at, city, gender
            FROM users
            WHERE employee_id = %s
        """, (employee_id,))
        row = cur.fetchone()
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))
 
def approve_manager_ticket(indent_id):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE travel_indents
            SET manager_approval_status='accepted_manager', updated_at=NOW()
            WHERE indent_id=%s
        """, (indent_id,))
        conn.commit()
        cur.close()
 
def reject_manager_ticket(indent_id):
    """Mark indent as manager Rejected"""
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE travel_indents
            SET is_approved = 'rejected_manager',
                updated_at = CURRENT_TIMESTAMP
            WHERE indent_id = %s
        """, (indent_id,))
        conn.commit()
        return True
 
def get_pending_hr_tickets():
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT indent_id, employee_id, purpose, start_date, end_date, total_estimated_cost
            FROM travel_indents
            WHERE manager_approval_status='APPROVED' AND hr_approval_status='PENDING'
        """)
        rows = cur.fetchall()
        cur.close()
    return [dict(zip(["indent_id","employee_id","purpose","start_date","end_date","total_estimated_cost"], r)) for r in rows]
 
def get_employee_by_indent(indent_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT u.employee_id, u.name, u.email, u.grade, u.department
            FROM users u JOIN travel_indents ti ON ti.employee_id = u.employee_id
            WHERE ti.indent_id=%s
        """, (indent_id,))
        row = cur.fetchone()
        cur.close()
    if not row:
        return None
    return dict(zip(["employee_id","name","email","grade","department"], row))
 
def approve_hr_ticket(indent_id: str, hr_id: str, comments: str | None = None):
    with get_db_conn() as conn:
        cur = conn.cursor()
        _require_manager_approval_for_hr(cur, indent_id)
        cur.execute("""
            UPDATE travel_indents
            SET hr_approval_status='APPROVED',
                status='HR_APPROVED',
                is_approved='hr_approved',
                updated_at=NOW()
            WHERE indent_id=%s
        """, (indent_id,))
        cur.execute("""
            UPDATE approval_workflow
            SET status='APPROVED', comments=%s, approved_at=NOW()
            WHERE indent_id=%s AND approver_id=%s AND approval_type='HR'
        """, (comments, indent_id, hr_id))
        conn.commit()
        cur.close()
 
def book_flight(indent_id: str):
    # demo: mark as booked and return booking id
    booking = {"booking_id": f"FL{indent_id[-6:]}", "airline": "Indigo", "flight": "6E-502", "status":"CONFIRMED"}
    with get_db_conn() as conn:
        cur = conn.cursor()
        _require_manager_approval_for_hr(cur, indent_id)
        cur.execute(
            "UPDATE travel_indents SET status='BOOKED', is_approved='booked', updated_at=NOW() WHERE indent_id=%s",
            (indent_id,),
        )
        conn.commit()
        cur.close()
    return booking
 
def book_hotel(indent_id: str):
    booking = {"booking_id": f"HT{indent_id[-6:]}", "hotel": "Tech Park Inn", "status":"CONFIRMED"}
    return booking
 
def create_travel_indent_from_form(
    employee_id: str,
    purpose_of_booking: str,
    travel_type: str,
    travel_start_date,  # date
    travel_end_date,  # date
    from_city: str,
    from_country: str,
    to_city: str,
    to_country: str,
    initial_status: str = "pending",
    indent_id: str | None = None,
):
    """
    Create or update a travel indent row using the logged-in employee details
    and the form data. Returns the indent_id (existing or newly created).
    """
    with get_db_conn() as conn:
        cur = conn.cursor()
 
        if indent_id:
            cur.execute(
                "SELECT employee_id, COALESCE(is_approved, 'pending') FROM travel_indents WHERE indent_id=%s",
                (indent_id,),
            )
            existing = cur.fetchone()
            if not existing:
                cur.close()
                raise ValueError("Draft travel indent not found")
 
            owner_id, existing_status = existing
            if owner_id != employee_id:
                cur.close()
                raise ValueError("You cannot modify another employee's indent")
 
            normalized_status = (existing_status or "draft").strip().lower()
            if normalized_status != "draft":
                cur.close()
                raise ValueError("Only draft indents can be edited via this flow")
 
            if initial_status != "draft":
                _ensure_no_duplicate_active(
                    cur,
                    employee_id,
                    from_city,
                    to_city,
                    travel_start_date,
                    travel_end_date,
                    exclude_indent_id=indent_id,
                )
 
            cur.execute(
                """
                UPDATE travel_indents
                SET purpose_of_booking = %s,
                    travel_type = %s,
                    travel_start_date = %s,
                    travel_end_date = %s,
                    from_city = %s,
                    from_country = %s,
                    to_city = %s,
                    to_country = %s,
                    is_approved = %s,
                    updated_at = NOW()
                WHERE indent_id = %s
                RETURNING indent_id;
                """,
                (
                    purpose_of_booking,
                    travel_type,
                    travel_start_date,
                    travel_end_date,
                    from_city,
                    from_country,
                    to_city,
                    to_country,
                    initial_status,
                    indent_id,
                ),
            )
 
            updated_indent_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            return updated_indent_id
 
        # inserting a brand new indent
        if initial_status != "draft":
            _ensure_no_duplicate_active(
                cur,
                employee_id,
                from_city,
                to_city,
                travel_start_date,
                travel_end_date,
            )
 
        cur.execute(
            """
            SELECT name, email, grade, department, designation
            FROM users
            WHERE employee_id = %s
            """,
            (employee_id,),
        )
        row = cur.fetchone()
        if not row:
            cur.close()
            raise ValueError(f"No user found with employee_id={employee_id}")
 
        employee_name, email, grade, department, designation = row
 
        indent_id = f"IND-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:6].upper()}"
 
        cur.execute(
            """
            INSERT INTO travel_indents (
                indent_id,
                employee_id,
                employee_name,
                email,
                grade,
                department,
                designation,
                purpose_of_booking,
                travel_type,
                travel_start_date,
                travel_end_date,
                from_city,
                from_country,
                to_city,
                to_country,
                is_approved
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING indent_id;
            """,
            (
                indent_id,
                employee_id,
                employee_name,
                email,
                grade,
                department,
                designation,
                purpose_of_booking,
                travel_type,
                travel_start_date,
                travel_end_date,
                from_city,
                from_country,
                to_city,
                to_country,
                initial_status,
            ),
        )
 
        new_indent_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return new_indent_id
 
def get_employee_travel_indents(employee_id: str):
    """
    Return all travel indents for the given employee, using the is_approved field
    from travel_indents (text: 'pending' / 'approved' / 'rejected' etc.).
    """
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                indent_id,
                travel_start_date,
                travel_end_date,
                from_city,
                from_country,
                to_city,
                to_country,
                travel_type,
                purpose_of_booking,
                is_approved,
                created_at
            FROM travel_indents
            WHERE employee_id = %s
            ORDER BY created_at DESC
            """,
            (employee_id,),
        )
        rows = cur.fetchall()
        cur.close()
 
    tickets = []
    for row in rows:
        (
            indent_id,
            travel_start_date,
            travel_end_date,
            from_city,
            from_country,
            to_city,
            to_country,
            travel_type,
            purpose_of_booking,
            is_approved,
            created_at,
        ) = row
 
        # produce a machine-friendly code and a readable label
        status_code = (is_approved or "pending").strip().lower()
        if status_code == "accepted_manager":
            status_clean = "Approved by manager (Pending HR)"
        elif status_code in ("completed_hr", "hr_approved", "booked", "hr_approved"):
            status_clean = "Completed booking"
        elif status_code == "rejected_manager":
            status_clean = "Rejected by manager"
        elif status_code == "rejected_hr":
            status_clean = "Rejected by HR"
        elif status_code == "draft":
            status_clean = "Draft"
        elif status_code in ("rejected", "declined"):
            status_clean = "Rejected"
        else:
            status_clean = "Pending"
 
        tickets.append(
            {
                "indent_id": indent_id,
                "travel_start_date": travel_start_date,
                "travel_end_date": travel_end_date,
                "from_city": from_city,
                "from_country": from_country,
                "to_city": to_city,
                "to_country": to_country,
                "travel_type": travel_type,
                "purpose_of_booking": purpose_of_booking,
                "status_code": status_code,
                "status": status_clean,
                "created_at": created_at,
            }
        )
 
    return tickets
 
 
def get_employee_route_bookmarks(employee_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                bookmark_id,
                employee_id,
                from_city,
                from_country,
                to_city,
                to_country,
                label,
                times_used,
                last_used_at,
                created_at
            FROM employee_route_bookmarks
            WHERE employee_id = %s
            ORDER BY COALESCE(last_used_at, created_at) DESC, created_at DESC
            """,
            (employee_id,),
        )
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        cur.close()
 
    return [dict(zip(cols, row)) for row in rows]
 
 
def create_employee_route_bookmark(
    employee_id: str,
    from_city: str,
    to_city: str,
    from_country: str | None = None,
    to_country: str | None = None,
    label: str | None = None,
):
    normalized_from = _normalize_place(from_city)
    normalized_to = _normalize_place(to_city)
    if not normalized_from or not normalized_to:
        raise ValueError("Both origin and destination cities are required to bookmark a route.")
 
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT bookmark_id
            FROM employee_route_bookmarks
            WHERE employee_id = %s
              AND LOWER(TRIM(COALESCE(from_city,''))) = %s
              AND LOWER(TRIM(COALESCE(to_city,''))) = %s
            LIMIT 1
            """,
            (employee_id, normalized_from, normalized_to),
        )
        exists = cur.fetchone()
        if exists:
            cur.close()
            raise ValueError("This route is already bookmarked.")
 
        bookmark_id = f"RT-{uuid.uuid4().hex[:8].upper()}"
        cur.execute(
            """
            INSERT INTO employee_route_bookmarks (
                bookmark_id,
                employee_id,
                from_city,
                from_country,
                to_city,
                to_country,
                label
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING bookmark_id;
            """,
            (
                bookmark_id,
                employee_id,
                from_city.strip(),
                (from_country or "India").strip(),
                to_city.strip(),
                (to_country or "India").strip(),
                (label or None),
            ),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
 
    return new_id
 
 
def delete_employee_route_bookmark(employee_id: str, bookmark_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM employee_route_bookmarks
            WHERE employee_id = %s AND bookmark_id = %s
            RETURNING bookmark_id
            """,
            (employee_id, bookmark_id),
        )
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
 
    if not deleted:
        raise ValueError("Bookmark not found")
    return True
 
 
def touch_employee_route_bookmark(employee_id: str, bookmark_id: str):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE employee_route_bookmarks
            SET times_used = COALESCE(times_used, 0) + 1,
                last_used_at = NOW()
            WHERE employee_id = %s AND bookmark_id = %s
            RETURNING bookmark_id
            """,
            (employee_id, bookmark_id),
        )
        updated = cur.fetchone()
        conn.commit()
        cur.close()
 
    if not updated:
        raise ValueError("Bookmark not found")
    return True
 
 
from src.db.connection import get_db_conn  # this should already be there
 
 
def get_employee_details(employee_id: str):
    """
    Fetch full employee profile from users table by employee_id.
    """
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    employee_id,
                    name,
                    email,
                    grade,
                    department,
                    designation
                FROM users
                WHERE employee_id = %s
                """,
                (employee_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
 
    if not row:
        return None
 
    (
        employee_id,
        name,
        email,
        grade,
        department,
        designation,
    ) = row
 
    return {
        "employee_id": employee_id,
        "name": name,
        "email": email,
        "grade": grade,
        "department": department,
        "designation": designation,
    }
 