from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from db.connection import get_db, Order, Bank

router = APIRouter(prefix="/orders", tags=["orders"])


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