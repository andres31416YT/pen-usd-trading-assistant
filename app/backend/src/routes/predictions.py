import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from db.connection import get_db, Prediction, Signal, SignalHistory, Alarm
from model_loader.load_model import get_model_loader
from market_data.yahoo import get_latest_price as yahoo_get_latest_price

router = APIRouter(prefix="/prediction", tags=["predictions"])


def _latest_market_price(pair: str) -> Optional[float]:
    symbol_map = {
        "PEN/USD": "PEN=X",
    }
    symbol = symbol_map.get(pair, pair)
    try:
        return yahoo_get_latest_price(symbol)
    except Exception as e:
        logger.warning("Yahoo Finance failed for %s (%s): %s", pair, symbol, e)
        return None


@router.get("/{pair}")
def get_prediction(
    pair: str,
    lookback_days: int = Query(default=30, ge=1, le=365),
    spread_multiplier: float = Query(default=1.0, ge=0.01),
    db: Session = Depends(get_db),
):
    loader = get_model_loader()
    result = loader.predict(pair, lookback_days, spread_multiplier=spread_multiplier)

    current_price = _latest_market_price(pair)

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

    return {
        "direction": result["direction"],
        "confidence": result["confidence"],
        "price_target": result["price_target"],
        "current_price": current_price,
        "model_version": result.get("model_version"),
        "spread_multiplier": spread_multiplier,
    }


@router.get("")
def get_latest_prediction(
    pair: Optional[str] = Query(default=None),
    spread_multiplier: float = Query(default=1.0, ge=0.01),
    db: Session = Depends(get_db),
):
    loader = get_model_loader()

    if pair:
        result = loader.predict(pair, spread_multiplier=spread_multiplier)
        current_price = _latest_market_price(pair)
        return {
            "direction": result["direction"],
            "confidence": result["confidence"],
            "price_target": result["price_target"],
            "current_price": current_price,
            "model_version": result.get("model_version"),
            "spread_multiplier": spread_multiplier,
        }

    pair = pair or "PEN/USD"

    result = loader.predict(pair, spread_multiplier=spread_multiplier)
    current_price = _latest_market_price(pair)

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

    return {
        "direction": result["direction"],
        "confidence": result["confidence"],
        "price_target": result["price_target"],
        "current_price": current_price,
        "model_version": result.get("model_version"),
        "pair": prediction.pair,
        "spread_multiplier": spread_multiplier,
    }