from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
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
        "DATABASE_URL is not set. Set DATABASE_URL, DATABASE_URL_AUTH, or DATABASE_URL_TRADING in environment or .env file."
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


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    price_target = Column(Float)
    model_version = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    current_price = Column(Float)
    target_price = Column(Float)
    indicator = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class SignalHistory(Base):
    __tablename__ = "signal_history"

    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    confidence = Column(Float, nullable=False)
    price_at_time = Column(Float)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold_price = Column(Float, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    pair = Column(String(20), nullable=False)
    alert_threshold = Column(Float)
    preferred_direction = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Bank(Base):
    __tablename__ = "banks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    spread_multiplier = Column(Float, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    pair = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    bank_id = Column(Integer, ForeignKey("banks.id"))
    status = Column(String(20), default="filled")
    created_at = Column(DateTime, default=datetime.utcnow)