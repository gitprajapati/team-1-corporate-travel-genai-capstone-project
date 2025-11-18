# src/api/employee_router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from src.auth.jwt_service import get_current_user
from datetime import date
from typing import Literal, Optional
from src.api.models import PolicyChatRequest, PolicyChatResponse
from src.db.travel_queries import (
    create_travel_indent_from_form,
    get_employee_travel_indents,
    get_employee_details,
    get_employee_route_bookmarks,
    create_employee_route_bookmark,
    delete_employee_route_bookmark,
    touch_employee_route_bookmark,
)
from src.rag.rag_service import get_policy_rag_service
router = APIRouter()
# In-memory session store (demo). Replace with Redis in prod.
SESSION_STORE = {}

class ChatReq(BaseModel):
    message: str



class TravelIndentCreate(BaseModel):
    purpose_of_booking: str
    travel_type: Literal["domestic", "international"]
    travel_start_date: date
    travel_end_date: date
    from_city: str
    from_country: str
    to_city: str
    to_country: str
    indent_id: Optional[str] = None


class RouteBookmarkCreate(BaseModel):
    from_city: str
    to_city: str
    from_country: Optional[str] = "India"
    to_country: Optional[str] = "India"
    label: Optional[str] = None

    @validator("from_city", "to_city")
    def not_blank(cls, value: str):  # pylint: disable=no-self-argument
        if not value or not value.strip():
            raise ValueError("City names cannot be empty")
        return value.strip()

    @validator("from_country", "to_country", pre=True, always=True)
    def default_country(cls, value):  # pylint: disable=no-self-argument
        if value is None or not str(value).strip():
            return "India"
        return str(value).strip()
@router.post("/create-indent")
def create_indent(
    req: TravelIndentCreate,
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    try:
        new_indent_id = create_travel_indent_from_form(
            employee_id=current_user["employee_id"],
            purpose_of_booking=req.purpose_of_booking,
            travel_type=req.travel_type,
            travel_start_date=req.travel_start_date,
            travel_end_date=req.travel_end_date,
            from_city=req.from_city,
            from_country=req.from_country,
            to_city=req.to_city,
            to_country=req.to_country,
            indent_id=req.indent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Travel ticket created successfully.",
        "indent_id": new_indent_id,
    }


@router.post("/save-draft")
def save_draft(
    req: TravelIndentCreate,
    current_user=Depends(get_current_user),
):
    """Save a travel indent as a draft (not submitted for approvals)."""
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    try:
        new_indent_id = create_travel_indent_from_form(
            employee_id=current_user["employee_id"],
            purpose_of_booking=req.purpose_of_booking,
            travel_type=req.travel_type,
            travel_start_date=req.travel_start_date,
            travel_end_date=req.travel_end_date,
            from_city=req.from_city,
            from_country=req.from_country,
            to_city=req.to_city,
            to_country=req.to_country,
            initial_status="draft",
            indent_id=req.indent_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Draft saved.", "indent_id": new_indent_id}


@router.post("/policy/chat", response_model=PolicyChatResponse)
async def chat_policy_assistant(
    request: PolicyChatRequest,
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    rag_service = get_policy_rag_service()
    try:
        result = await rag_service.chat(
            message=request.message,
            session_id=request.session_id,
        )
        return PolicyChatResponse(**result)
    except ValueError as validation_error:
        raise HTTPException(status_code=400, detail=str(validation_error))
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Policy assistant error: {exc}")
@router.get("/my-indents")
def list_my_indents(current_user=Depends(get_current_user)):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    tickets = get_employee_travel_indents(current_user["employee_id"])
    return {"items": tickets}
@router.get("/profile")
def profile(current_user=Depends(get_current_user)):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    emp_id = current_user["employee_id"]
    details = get_employee_details(emp_id)
    if not details:
        raise HTTPException(status_code=404, detail="Employee profile not found")

    return details


@router.get("/frequent-routes")
def list_route_bookmarks(current_user=Depends(get_current_user)):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    bookmarks = get_employee_route_bookmarks(current_user["employee_id"])
    return {"items": bookmarks}


@router.post("/frequent-routes")
def add_route_bookmark(
    request: RouteBookmarkCreate,
    current_user=Depends(get_current_user),
):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    try:
        bookmark_id = create_employee_route_bookmark(
            employee_id=current_user["employee_id"],
            from_city=request.from_city,
            to_city=request.to_city,
            from_country=request.from_country,
            to_country=request.to_country,
            label=request.label,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"bookmark_id": bookmark_id}


@router.delete("/frequent-routes/{bookmark_id}")
def remove_route_bookmark(bookmark_id: str, current_user=Depends(get_current_user)):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    try:
        delete_employee_route_bookmark(current_user["employee_id"], bookmark_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"message": "Bookmark deleted"}


@router.post("/frequent-routes/{bookmark_id}/use")
def mark_route_bookmark_used(bookmark_id: str, current_user=Depends(get_current_user)):
    if current_user["role"] != "employee":
        raise HTTPException(status_code=403, detail="Not an employee")

    try:
        touch_employee_route_bookmark(current_user["employee_id"], bookmark_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"message": "Bookmark usage recorded"}
