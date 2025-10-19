import argparse
from sqlmodel import Session, select

from .db import ENGINE, create_db_and_tables
from .models import User
from passlib.context import CryptContext


def main():
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("--full-name", default="")
    args = parser.parse_args()

    create_db_and_tables()
    # Use pbkdf2 to avoid bcrypt backend issues in some environments
    _ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    hashed = _ctx.hash(args.password)
    with Session(ENGINE) as session:
        exists = session.exec(select(User).where(User.username == args.username)).first()
        if exists:
            print("User already exists")
            return
        user = User(username=args.username, password_hash=hashed, role="admin", full_name=args.full_name)
        session.add(user)
        session.commit()
        print("Admin user created")


if __name__ == "__main__":
    main()
