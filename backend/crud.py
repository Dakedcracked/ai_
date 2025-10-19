from typing import Optional, List
from sqlmodel import Session, select

from .models import User, CompanyProfile


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()


def create_user(session: Session, username: str, password_hash: str, full_name: str = "", role: str = "doctor") -> User:
    user = User(username=username, password_hash=password_hash, full_name=full_name, role=role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def list_users(session: Session) -> List[User]:
    return list(session.exec(select(User)))


def set_user_role(session: Session, username: str, role: str) -> Optional[User]:
    user = get_user_by_username(session, username)
    if not user:
        return None
    user.role = role
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def upsert_company_profile(session: Session, name: str, address: str = "", contact_email: str = "", logo_url: str = "") -> CompanyProfile:
    profile = session.exec(select(CompanyProfile)).first()
    if not profile:
        profile = CompanyProfile(name=name, address=address, contact_email=contact_email, logo_url=logo_url)
        session.add(profile)
    else:
        profile.name = name
        profile.address = address
        profile.contact_email = contact_email
        profile.logo_url = logo_url
    session.commit()
    session.refresh(profile)
    return profile


def get_company_profile(session: Session) -> Optional[CompanyProfile]:
    return session.exec(select(CompanyProfile)).first()
