# src/api/services/context_service.py
"""
Context building for chat messages
"""
from typing import Optional, Dict

def build_context_message(user_message: str, travel_indent: Optional[Dict]) -> str:
    """Build enhanced message with travel context"""
    if not travel_indent:
        return user_message
    
    indent = travel_indent
    context_parts = []
    
    context_parts.append("📋 **EMPLOYEE INFORMATION:**")
    context_parts.append(f"👤 Name: {indent['employee_name']}")
    context_parts.append(f"🆔 ID: {indent['employee_id']}")
    context_parts.append(f"📊 Grade: {indent['grade']}")
    context_parts.append(f"💼 Designation: {indent['designation']}")
    context_parts.append(f"🏢 Department: {indent['department']}")
    context_parts.append(f"📧 Email: {indent['email']}")
    context_parts.append("")

    context_parts.append("🌍 **TRAVEL INFORMATION:**")
    context_parts.append(f"🎫 Type: {indent['travel_type']}")
    context_parts.append(f"🛫 From: {indent['from_city']}, {indent['from_country']}")
    context_parts.append(f"🛬 To: {indent['to_city']}, {indent['to_country']}")
    context_parts.append(f"📅 Start: {indent['travel_start_date']}")
    context_parts.append(f"📅 End: {indent['travel_end_date']}")
    context_parts.append(f"📝 Purpose: {indent['purpose_of_booking']}")
    context_parts.append(f"🎫 Ticket ID: {indent['indent_id']}")
    context_parts.append(f"📅 Total Days: {indent['total_days']}")
    context_parts.append("")

    context_parts.append("✅ **APPROVAL STATUS:**")
    status_mapping = {
        "saved": "Saved by Employee",
        "pending": "Pending Manager Approval",
        "rejected_manager": "Rejected by Manager",
        "accpeted_manager": "Approved by Manager",
        "accepted_manager": "Approved by Manager",
        "rejected_hr": "Rejected by HR",
        "completed_hr": "Completed by HR"
    }
    status_display = status_mapping.get(indent['is_approved'], indent['is_approved'])
    context_parts.append(f"Status: {status_display}")
    context_parts.append("")

    context_parts.append("---")
    context_parts.append(f"**USER REQUEST:** {user_message}")
    
    return "\n".join(context_parts)