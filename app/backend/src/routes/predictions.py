from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from db.connection import get_db, Prediction, Signal, SignalHistory, Alarm
from model_loader.load_model import get_model_loader

router = APIRouter(prefix="/prediction", tags=["predictions"])


@router.get("/{pair}")
def get_prediction(
    pair: str,
    lookback_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    loader = get_model_loader()
    result = loader.predict(pair, lookback_days)

    prediction = Prediction(
        pair=pair,
        direction=result["direction"],
        confidence=result["confidence"],
        price_target=result["price_target"],
        model_version=result.get("model_version"),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return result


@router.get("")
def get_latest_prediction(
    pair: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    loader = get_model_loader()

    if pair:
        result = loader.predict(pair)
        return result

    query = db.query(Prediction).order_by(Prediction.created_at.desc())
    latest = query.first()

    if latest is None:
        return {
            "direction": "neutral",
            "confidence": 0.0,
            "price_target": None,
            "model_version": None,
        }

    return {
        "direction": latest.direction,
        "confidence": latest.confidence,
        "price_target": latest.price_target,
        "model_version": latest.model_version,
        "pair": latest.pair,
    }