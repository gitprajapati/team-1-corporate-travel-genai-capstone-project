# src/api/auth_router.py
from datetime import datetime, timezone
from typing import Literal

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from src.auth.jwt_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    decode_token,
    get_current_user,
    oauth2_scheme,
    revoke_token,
)
from src.db.user_queries import check_user_exists, create_user

router = APIRouter()


class RegisterRequest(BaseModel):
    employee_id: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    grade: str | None = None
    role: Literal["employee", "manager", "hr"] = "employee"
    department: str | None = None
    designation: str | None = None
    manager_id: str | None = None
    city: str | None = None
    gender: str | None = None


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["employee_id"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "employee_id": user["employee_id"],
        "role": user["role"],
        "name": user["name"],
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    if check_user_exists(payload.employee_id, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with same employee ID or email already exists",
        )

    password_hash = bcrypt.hashpw(
        payload.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    user = create_user(
        employee_id=payload.employee_id.strip(),
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=password_hash,
        grade=payload.grade,
        role=payload.role,
        department=payload.department,
        designation=payload.designation,
        manager_id=payload.manager_id,
        city=payload.city,
        gender=payload.gender,
    )

    access_token = create_access_token(
        data={"sub": user["employee_id"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "employee_id": user["employee_id"],
        "role": user["role"],
        "name": user["name"],
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token, verify_revocation=True)
    jti = payload.get("jti")
    exp_ts = payload.get("exp")

    if not jti or not exp_ts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token payload missing identifiers",
        )

    revoke_token(jti, datetime.fromtimestamp(exp_ts, tz=timezone.utc))

    return {"message": "Logged out"}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return current_user
