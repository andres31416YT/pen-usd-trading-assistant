from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

from db.connection import get_db, Base, engine
from model_loader.load_model import get_model_loader
from routes.predictions import router as prediction_router
from routes.senales import router as signals_router
from routes.historico import router as history_router
from routes.banks import router as banks_router
from routes.orders import router as orders_router
from routes.account import router as account_router

app = FastAPI(
    title="PEN/USD Trading Backend",
    version="1.0.0",
    description="Backend de negocio para el asistente de trading PEN/USD"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    _seed_banks()


def _seed_banks():
    from db.connection import SessionLocal, Bank
    db = SessionLocal()
    try:
        existing = db.query(Bank).count()
        if existing == 0:
            bcp = Bank(name="BCP", spread_multiplier=3.40 / 3.760)
            db.add(bcp)
            db.commit()
    finally:
        db.close()

app.include_router(prediction_router)
app.include_router(signals_router)
app.include_router(history_router)
app.include_router(banks_router)
app.include_router(orders_router)
app.include_router(account_router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    loader = get_model_loader()
    model_loaded = loader.model is not None

    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "model_version": loader.model_version,
        "database": db_status,
    }