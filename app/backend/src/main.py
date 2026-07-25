from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from db.connection import get_db
from model_loader.load_model import get_model_loader
from routes.predictions import router as prediction_router
from routes.senales import router as signals_router
from routes.historico import router as history_router

app = FastAPI(
    title="PEN/USD Trading Backend",
    version="1.0.0",
    description="Backend de negocio para el asistente de trading PEN/USD"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_router)
app.include_router(signals_router)
app.include_router(history_router)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    loader = get_model_loader()
    model_loaded = loader.model is not None

    try:
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "model_version": loader.model_version,
        "database": db_status,
    }