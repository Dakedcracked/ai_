from datetime import datetime, timedelta
from typing import Optional
import os

from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Read secret from environment with safe fallback for local dev
SECRET_KEY = os.environ.get("ONCOSCAN_SECRET_KEY", "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_FOR_DEVELOPMENT")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ONCOSCAN_TOKEN_EXPIRE_MINUTES", 60 * 24))  # default 24 hours

pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Simulated user DB
# Hashing with bcrypt at module import can cause environment-specific issues
# (bcrypt binary backend problems). For a reliable local demo we precompute a
# pbkdf2_sha256 hash here. In production you should store bcrypt hashes
# generated at user-creation time.
_pbkdf_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
_demo_hash = _pbkdf_ctx.hash("securepass")

FAKE_USERS_DB = {
    "doc_user": {
        "user_id": "doc_user",
        # demo hashed password (pbkdf2_sha256) to avoid bcrypt import-time issues
        "hashed_password": _demo_hash,
        "full_name": "Dr. Alice Onco",
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # First try DB-backed user
    try:
        from .db import get_session
        from .models import User
        from sqlmodel import select
        with next(get_session()) as session:  # type: ignore
            db_user = session.exec(select(User).where(User.username == user_id)).first()
            if db_user:
                if db_user.disabled:
                    raise HTTPException(status_code=400, detail="Inactive user")
                return {"user_id": db_user.username, "username": db_user.full_name or db_user.username, "role": db_user.role}
    except Exception:
        pass

    # Fallback to in-memory demo user
    user = FAKE_USERS_DB.get(user_id)
    if user is None:
        raise credentials_exception
    if user.get("disabled"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return {"user_id": user_id, "username": user.get("full_name"), "role": "doctor"}
