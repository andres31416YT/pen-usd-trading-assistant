from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from db.connection import get_db, SignalHistory, Prediction

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/signals")
def get_signal_history(
    pair: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    query = db.query(SignalHistory).filter(
        SignalHistory.created_at >= since
    )
    if pair:
        query = query.filter(SignalHistory.pair == pair)

    history = query.order_by(SignalHistory.created_at.desc()).limit(limit).all()

    return [
        {
            "id": h.id,
            "pair": h.pair,
            "direction": h.direction,
            "confidence": h.confidence,
            "price_at_time": h.price_at_time,
            "source": h.source,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]


@router.get("/predictions")
def get_prediction_history(
    pair: Optional[str] = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    query = db.query(Prediction).filter(
        Prediction.created_at >= since
    )
    if pair:
        query = query.filter(Prediction.pair == pair)

    history = query.order_by(Prediction.created_at.desc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "pair": p.pair,
            "direction": p.direction,
            "confidence": p.confidence,
            "price_target": p.price_target,
            "model_version": p.model_version,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in history
    ]