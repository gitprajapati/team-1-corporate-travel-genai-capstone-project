# src/auth/jwt_service.py
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Optional
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.db.connection import get_db_conn
from src.config.settings import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# -----------------------------------------------------
# TOKEN BLACKLIST (in-memory; replace with Redis/DB in prod)
# -----------------------------------------------------
_TOKEN_BLACKLIST: dict[str, datetime] = {}
_TOKEN_LOCK = Lock()


def _cleanup_expired_tokens():
    now = datetime.now(timezone.utc)
    with _TOKEN_LOCK:
        expired = [jti for jti, exp in _TOKEN_BLACKLIST.items() if exp <= now]
        for jti in expired:
            _TOKEN_BLACKLIST.pop(jti, None)


def revoke_token(jti: str, expires_at: datetime):
    """Mark a token's JTI as revoked until its natural expiry."""
    if not jti:
        return
    _cleanup_expired_tokens()
    with _TOKEN_LOCK:
        _TOKEN_BLACKLIST[jti] = expires_at


def is_token_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return False
    _cleanup_expired_tokens()
    expires_at = _TOKEN_BLACKLIST.get(jti)
    if not expires_at:
        return False
    if expires_at <= datetime.now(timezone.utc):
        with _TOKEN_LOCK:
            _TOKEN_BLACKLIST.pop(jti, None)
        return False
    return True


# -----------------------------------------------------
# FIXED → can search user by email OR employee_id
# -----------------------------------------------------
def get_user_by_identifier(identifier: str):
    print("Fetching user by identifier:", identifier)

    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT employee_id, name, email, password_hash, grade, role, is_active
            FROM users
            WHERE email = %s OR employee_id = %s
        """, (identifier, identifier))
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
    }


# -----------------------------------------------------
# AUTH HELPERS
# -----------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    )

    to_encode.update({
        "exp": expire,
        "jti": uuid4().hex,
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(identifier: str, password: str):
    rec = get_user_by_identifier(identifier)
    if not rec:
        return None

    if not rec["password_hash"]:
        return None

    if not verify_password(password, rec["password_hash"]):
        return None

    return {
        "employee_id": rec["employee_id"],
        "name": rec["name"],
        "email": rec["email"],
        "grade": rec["grade"],
        "role": rec["role"],
        "is_active": rec["is_active"]
    }


def decode_token(token: str, *, verify_revocation: bool = True):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    if verify_revocation:
        if is_token_revoked(payload.get("jti")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked",
            )

    return payload


def verify_token(token: str):
    return decode_token(token, verify_revocation=True)


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)

    identifier = payload.get("sub")
    if not identifier:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_identifier(identifier)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")

    return {
        "employee_id": user["employee_id"],
        "name": user["name"],
        "email": user["email"],
        "grade": user["grade"],
        "role": user["role"],
    }
