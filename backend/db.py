import os
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine


def get_database_url() -> str:
    # Prefer Postgres; example: postgresql+psycopg2://user:pass@localhost:5432/oncoscan
    url = os.environ.get("ONCOSCAN_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if url:
        return url
    # Fallback to local SQLite for development if not provided
    return "sqlite:///oncoscan_webapp/backend/oncoscan.db"


ENGINE = create_engine(get_database_url(), echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(ENGINE)


def get_session() -> Generator[Session, None, None]:
    with Session(ENGINE) as session:
        yield session
