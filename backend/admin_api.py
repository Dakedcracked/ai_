from typing import List, Optional
import os
import csv
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from .db import get_session
from .crud import list_users, set_user_role, create_user, upsert_company_profile, get_company_profile
from .models import User
from .auth import get_current_user, pwd_context


def require_admin(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return current_user


def require_doctor(current_user = Depends(get_current_user)):
    if current_user.get("role") != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor role required")
    return current_user


class UserIn(BaseModel):
    username: str
    full_name: Optional[str] = ""
    password: str
    role: str = "doctor"


class CompanyIn(BaseModel):
    name: str
    address: Optional[str] = ""
    contact_email: Optional[str] = ""
    logo_url: Optional[str] = ""


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[User])
def admin_list_users(_: dict = Depends(require_admin), session: Session = Depends(get_session)):
    return list_users(session)


@router.post("/users", response_model=User)
def admin_create_user(payload: UserIn, _: dict = Depends(require_admin), session: Session = Depends(get_session)):
    hashed = pwd_context.hash(payload.password)
    return create_user(session, payload.username, hashed, payload.full_name or "", payload.role)


@router.post("/users/{username}/role", response_model=User)
def admin_set_role(username: str, role: str, _: dict = Depends(require_admin), session: Session = Depends(get_session)):
    user = set_user_role(session, username, role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/company", response_model=dict)
def admin_upsert_company(payload: CompanyIn, _: dict = Depends(require_admin), session: Session = Depends(get_session)):
    prof = upsert_company_profile(session, payload.name, payload.address or "", payload.contact_email or "", payload.logo_url or "")
    return {"status": "ok", "company_id": prof.id}


@router.get("/company", response_model=dict)
def admin_get_company(_: dict = Depends(require_admin), session: Session = Depends(get_session)):
    prof = get_company_profile(session)
    if not prof:
        return {"company": None}
    return {
        "company": {
            "id": prof.id,
            "name": prof.name,
            "address": prof.address,
            "contact_email": prof.contact_email,
            "logo_url": prof.logo_url,
        }
    }


@router.get("/audits", response_model=List[dict])
def admin_list_audits(limit: int = 50, _: dict = Depends(require_admin)):
    audit_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'audit_log.csv'))
    rows: List[dict] = []
    if not os.path.exists(audit_csv):
        return rows
    with open(audit_csv, 'r', newline='') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        rows = all_rows[-limit:]
    return rows
