from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from db.connection import get_db, Order, Bank

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderRequest(BaseModel):
    pair: str
    side: str
    amount: float
    price: float
    bank_id: int = None


def _get_balances(db: Session):
    orders = db.query(Order).all()
    usd_balance = 10000.0
    pen_balance = 0.0
    for o in orders:
        if o.side == "buy":
            usd_balance -= o.amount * o.price
            pen_balance += o.amount
        elif o.side == "sell":
            usd_balance -= o.amount
            pen_balance += o.amount / o.price
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
    order_data: OrderRequest,
    db: Session = Depends(get_db),
):
    usd_balance, pen_balance = _get_balances(db)

    if order_data.side == "buy":
        cost_usd = order_data.amount * order_data.price
        if cost_usd > usd_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente en USD. Necesitas {cost_usd:.2f} USD pero solo tienes {usd_balance:.2f} USD.",
            )
    elif order_data.side == "sell":
        if order_data.amount > usd_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Saldo insuficiente en USD. Quieres vender {order_data.amount:.2f} USD pero solo tienes {usd_balance:.2f} USD.",
            )
    else:
        raise HTTPException(status_code=400, detail=f"Lado inválido: {order_data.side}. Debe ser 'buy' o 'sell'.")

    order = Order(
        user_id=1,
        pair=order_data.pair,
        side=order_data.side,
        amount=order_data.amount,
        price=order_data.price,
        bank_id=order_data.bank_id,
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