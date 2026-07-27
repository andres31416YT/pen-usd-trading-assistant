from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from db.connection import get_db, Order, Bank

router = APIRouter(prefix="/orders", tags=["orders"])


def _get_balances(db: Session):
    orders = db.query(Order).all()
    usd_balance = 10000.0
    pen_balance = 0.0
    for o in orders:
        if o.side == "buy":
            usd_balance -= o.amount * o.price
            pen_balance += o.amount
        elif o.side == "sell":
            usd_balance += o.amount * o.price
            pen_balance -= o.amount
    return usd_balance, pen_balance


@router.get("")
def list_orders(
    pair: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Order).order_by(Order.created_at.desc())
    if pair:
        query = query.filter(Order.pair == pair)
    orders = query.limit(50).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "pair": o.pair,
            "side": o.side,
            "amount": o.amount,
            "price": o.price,
            "bank_id": o.bank_id,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


@router.post("")
def create_order(
    pair: str,
    side: str,
    amount: float,
    price: float,
    bank_id: int = None,
    db: Session = Depends(get_db),
):
    usd_balance, pen_balance = _get_balances(db)

    if side == "buy":
        cost_usd = amount * price
        if cost_usd > usd_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente en USD. Necesitas {cost_usd:.2f} USD pero solo tienes {usd_balance:.2f} USD.",
            )
    elif side == "sell":
        if amount > pen_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente en PEN. Quieres vender {amount:.2f} PEN pero solo tienes {pen_balance:.2f} PEN.",
            )
    else:
        raise HTTPException(status_code=400, detail=f"Lado inválido: {side}. Debe ser 'buy' o 'sell'.")

    order = Order(
        user_id=1,
        pair=pair,
        side=side,
        amount=amount,
        price=price,
        bank_id=bank_id,
        status="filled",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "id": order.id,
        "pair": order.pair,
        "side": order.side,
        "amount": order.amount,
        "price": order.price,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }