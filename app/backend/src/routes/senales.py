from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from db.connection import get_db, Signal, SignalHistory, Alarm, UserPreference
from model_loader.load_model import get_model_loader

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/")
def get_signals(
    pair: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    loader = get_model_loader()

    query = db.query(Signal).order_by(Signal.created_at.desc())
    if pair:
        query = query.filter(Signal.pair == pair)

    signals = query.limit(limit).all()

    if not signals:
        pairs = [pair] if pair else ["PEN/USD"]
        for p in pairs:
            result = loader.generate_signal(p)
            signal = Signal(
                pair=result["pair"],
                direction=result["direction"],
                confidence=result["confidence"],
                current_price=result["current_price"],
                target_price=result["target_price"],
                indicator=result["indicator"],
            )
            db.add(signal)
            db.commit()
            db.refresh(signal)

        query = db.query(Signal).order_by(Signal.created_at.desc())
        if pair:
            query = query.filter(Signal.pair == pair)
        signals = query.limit(limit).all()

    return [
        {
            "id": s.id,
            "pair": s.pair,
            "direction": s.direction,
            "confidence": s.confidence,
            "current_price": s.current_price,
            "target_price": s.target_price,
            "indicator": s.indicator,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in signals
    ]


@router.get("/alarms")
def get_alarms(
    pair: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Alarm).filter(Alarm.is_active == 1)
    if pair:
        query = query.filter(Alarm.pair == pair)

    alarms = query.all()

    return [
        {
            "id": a.id,
            "pair": a.pair,
            "condition": a.condition,
            "threshold_price": a.threshold_price,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alarms
    ]


@router.post("/alarms")
def create_alarm(
    pair: str,
    condition: str,
    threshold_price: float,
    db: Session = Depends(get_db),
):
    alarm = Alarm(
        pair=pair,
        condition=condition,
        threshold_price=threshold_price,
        is_active=1,
    )
    db.add(alarm)
    db.commit()
    db.refresh(alarm)

    return {
        "id": alarm.id,
        "pair": alarm.pair,
        "condition": alarm.condition,
        "threshold_price": alarm.threshold_price,
        "message": "Alarma creada correctamente",
    }


@router.delete("/alarms/{alarm_id}")
def delete_alarm(alarm_id: int, db: Session = Depends(get_db)):
    alarm = db.query(Alarm).filter(Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarma no encontrada")

    alarm.is_active = 0
    db.commit()

    return {"message": "Alarma desactivada"}