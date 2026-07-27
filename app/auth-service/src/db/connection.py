from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URL_AUTH")
    or os.getenv("DATABASE_URL_TRADING")
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Set DATABASE_URL, DATABASE_URL_AUTH, or DATABASE_URL_TRADER in environment or .env file."
    )

MAX_DB_RETRIES = 5
RETRY_DELAY = 2

engine = None
for attempt in range(1, MAX_DB_RETRIES + 1):
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        engine.connect()
        break
    except Exception as e:
        if attempt == MAX_DB_RETRIES:
            raise RuntimeError(
                f"Failed to connect to database after {MAX_DB_RETRIES} attempts. URL: {DATABASE_URL[:50]}... Error: {e}"
            ) from e
        time.sleep(RETRY_DELAY * attempt)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()