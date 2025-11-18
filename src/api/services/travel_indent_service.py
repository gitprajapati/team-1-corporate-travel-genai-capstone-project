# src/api/services/travel_indent_service.py
"""
Travel indent database operations
"""
from typing import Optional, Dict, List
from src.db.connection import get_db_conn

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

class TravelIndentService:
    """Service for travel indent operations"""
    
    @staticmethod
    def get_by_id(indent_id: str) -> Optional[Dict]:
        """Get travel indent from database"""
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT indent_id, employee_id, employee_name, email, grade, department,
                       designation, purpose_of_booking, travel_type, travel_start_date,
                       travel_end_date, from_city, from_country, to_city, to_country,
                       total_days, is_approved, created_at
                FROM travel_indents 
                WHERE indent_id = %s
            """, (indent_id,))
            row = cur.fetchone()
            cur.close()
        
        if not row:
            return None
        
        return {
            "indent_id": row[0],
            "employee_id": row[1],
            "employee_name": row[2],
            "email": row[3],
            "grade": row[4],
            "department": row[5],
            "designation": row[6],
            "purpose_of_booking": row[7],
            "travel_type": row[8],
            "travel_start_date": row[9],
            "travel_end_date": row[10],
            "from_city": row[11],
            "from_country": row[12],
            "to_city": row[13],
            "to_country": row[14],
            "total_days": row[15],
            "is_approved": row[16],
            "created_at": row[17]
        }
    
    @staticmethod
    def update_status(indent_id: str, status: str) -> bool:
        """Update travel indent status"""
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(is_approved, 'pending') FROM travel_indents WHERE indent_id=%s",
                (indent_id,),
            )
            row = cur.fetchone()
            if not row:
                cur.close()
                return False

            current_status = (row[0] or "pending").strip().lower()
            normalized_new = (status or "").strip().lower()
            if normalized_new in _HR_ACTION_STATUSES and current_status not in _HR_ELIGIBLE_STATUSES:
                cur.close()
                raise ValueError("Manager approval required before HR can approve or book this ticket.")

            cur.execute("""
                UPDATE travel_indents 
                SET is_approved = %s, updated_at = NOW() 
                WHERE indent_id = %s
            """, (status, indent_id))
            conn.commit()
            success = cur.rowcount > 0
            cur.close()
            return success
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Get all travel indents for HR dashboard"""
        with get_db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
          SELECT indent_id, employee_id, employee_name, email, grade, department,
              designation, purpose_of_booking, travel_type, travel_start_date,
              travel_end_date, from_city, from_country, to_city, to_country,
              total_days, is_approved,
              COALESCE(is_approved, 'pending') AS status_code,
              created_at
                FROM travel_indents 
                WHERE COALESCE(is_approved, 'pending') IN (
                    'pending', 'manager_pending', 'pending_manager', 'submitted',
                    'accepted_manager', 'accpeted_manager', 'manager_approved',
                    'hr_approved', 'completed_hr', 'booked'
                )
                ORDER BY created_at DESC
            """)
            rows = cur.fetchall()
            cur.close()
        
        result = []
        for row in rows:
            result.append({
                "indent_id": row[0],
                "employee_id": row[1],
                "employee_name": row[2],
                "email": row[3],
                "grade": row[4],
                "department": row[5],
                "designation": row[6],
                "purpose_of_booking": row[7],
                "travel_type": row[8],
                "travel_start_date": row[9],
                "travel_end_date": row[10],
                "from_city": row[11],
                "from_country": row[12],
                "to_city": row[13],
                "to_country": row[14],
                "total_days": row[15],
                "is_approved": row[16],
                "status": row[17],
                "status_code": row[17],
                "created_at": row[18]
            })
        
        return result

# Singleton instance
_travel_indent_service: Optional[TravelIndentService] = None

def get_travel_indent_service() -> TravelIndentService:
    """Get travel indent service"""
    if not _travel_indent_service:
        return TravelIndentService()
    return _travel_indent_service