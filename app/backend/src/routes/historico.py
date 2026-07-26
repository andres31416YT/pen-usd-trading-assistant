from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import math

from db.connection import get_db, SignalHistory, Prediction, Order
from market_data.yahoo import get_price_history as yahoo_get_price_history

router = APIRouter(prefix="/history", tags=["history"])


def _generate_price_series(pair, days, num_points=80):
    base_prices = {
        "PEN/USD": 3.70,
    }
    base = base_prices.get(pair, 1.0)
    now = datetime.utcnow()
    points = []
    for i in range(num_points):
        d = now - timedelta(days=days - (i / max(num_points - 1, 1)) * days)
        t = i * 0.12
        drift = math.sin(t) * 0.025 + math.cos(t * 0.6) * 0.015
        price = base + drift
        points.append({
            "date": d.isoformat(),
            "pair": pair,
            "price": round(price, 4),
        })
    return points


TIMEFRAME_DAYS = {
    "1D": 1,
    "5D": 5,
    "1M": 30,
    "1Y": 365,
    "5Y": 1825,
    "Max": 3650,
}


@router.get("/prices")
def get_price_history(
    pair: Optional[str] = Query(default="PEN/USD"),
    timeframe: str = Query(default="5D"),
    pair_query: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    effective_pair = pair_query or pair or "PEN/USD"
    since = datetime.utcnow() - timedelta(days=TIMEFRAME_DAYS.get(timeframe, 30))

    orders = db.query(Order).filter(
        Order.pair == effective_pair,
        Order.created_at >= since,
    ).order_by(Order.created_at.asc()).all()

    if orders:
        data = [
            {
                "date": o.created_at.isoformat(),
                "pair": o.pair,
                "price": o.price,
            }
            for o in orders
        ]
        return {"pair": effective_pair, "data": data, "source": "orders"}

    try:
        symbol_map = {
            "PEN/USD": "PEN=X",
        }
        symbol = symbol_map.get(effective_pair, effective_pair)
        data = yahoo_get_price_history(symbol=symbol, timeframe=timeframe)
        return {"pair": effective_pair, "data": data, "source": "yahoo"}
    except Exception:
        pass

    data = _generate_price_series(effective_pair, TIMEFRAME_DAYS.get(timeframe, 30), 80)
    return {"pair": effective_pair, "data": data, "source": "synthetic"}


@router.get("")
def get_history_index(
    pair: Optional[str] = Query(default="PEN/USD"),
    timeframe: str = Query(default="5D"),
    pair_query: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_price_history(pair=pair, timeframe=timeframe, pair_query=pair_query, db=db)


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