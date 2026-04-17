from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import OUTPUTS_DIR


def database_url() -> str:
    default_path = OUTPUTS_DIR / "workbench.db"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return os.getenv("SCNU_DATABASE_URL", f"sqlite:///{default_path}").strip()


class Base(DeclarativeBase):
    pass


DATABASE_URL = database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    # Import models before create_all so SQLAlchemy registers metadata.
    from . import models as _models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    init_db()
    with SessionLocal() as session:
        yield session
