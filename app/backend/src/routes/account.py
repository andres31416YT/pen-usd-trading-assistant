from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from db.connection import get_db, Order, Bank

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/balance")
def get_balance(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    balance = 10000.0
    for o in orders:
        if o.side == "buy":
            balance -= o.amount * o.price
        elif o.side == "sell":
            balance += o.amount * o.price
    return {
        "balance": round(balance, 2),
        "currency": "USD",
        "initial_balance": 10000.0,
    }


@router.get("/balance-history")
def get_balance_history(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    orders = db.query(Order).filter(Order.created_at >= since).order_by(Order.created_at.asc()).all()
    balance = 10000.0
    history = []
    if not orders:
        history.append({"date": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d"), "balance": round(balance, 2)})
        for i in range(days):
            d = datetime.utcnow() - timedelta(days=days - 1 - i)
            history.append({"date": d.strftime("%Y-%m-%d"), "balance": round(balance, 2)})
        return history

    day_balances = {}
    for o in orders:
        date_key = o.created_at.strftime("%Y-%m-%d")
        if date_key not in day_balances:
            day_balances[date_key] = 0
        if o.side == "buy":
            day_balances[date_key] -= o.amount * o.price
        elif o.side == "sell":
            day_balances[date_key] += o.amount * o.price

    start_date = datetime.utcnow() - timedelta(days=days)
    current_date = start_date
    while current_date <= datetime.utcnow():
        key = current_date.strftime("%Y-%m-%d")
        balance += day_balances.get(key, 0)
        history.append({"date": key, "balance": round(balance, 2)})
        current_date += timedelta(days=1)

    return history


@router.get("/optimal-trade")
def get_optimal_trade(db: Session = Depends(get_db)):
    from model_loader.load_model import get_model_loader
    loader = get_model_loader()
    prediction = loader.predict("PEN/USD")
    direction = prediction.get("direction", "neutral")
    confidence = prediction.get("confidence", 0.0)
    is_optimal = confidence >= 0.6 and direction != "neutral"
    return {
        "recommendation": direction if is_optimal else "none",
        "confidence": confidence,
        "is_optimal": is_optimal,
        "optimal_price": prediction.get("price_target"),
        "price_target": prediction.get("price_target"),
    }