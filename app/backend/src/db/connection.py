from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/trading?schema=trading")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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