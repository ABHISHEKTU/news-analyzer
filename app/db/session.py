# app/db/session.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
from app.core.config import settings

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

try:
    Base.metadata.create_all(engine)
except (IntegrityError, ProgrammingError) as e:
    logger.warning(f"Table creation race (likely harmless, tables already exist): {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()