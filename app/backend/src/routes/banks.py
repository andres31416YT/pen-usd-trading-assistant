from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.connection import get_db, Bank

router = APIRouter(prefix="/banks", tags=["banks"])

BANK_SPREAD_MULTIPLIERS = {
    "BCP": 3.40 / 3.760,
}


@router.get("")
def list_banks(db: Session = Depends(get_db)):
    banks = db.query(Bank).all()
    if not banks:
        for name, multiplier in BANK_SPREAD_MULTIPLIERS.items():
            bank = Bank(name=name, spread_multiplier=multiplier)
            db.add(bank)
        db.commit()
        banks = db.query(Bank).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "spread_multiplier": b.spread_multiplier,
            "is_active": b.is_active,
        }
        for b in banks
    ]


@router.get("/{bank_id}")
def get_bank(bank_id: int, db: Session = Depends(get_db)):
    bank = db.query(Bank).filter(Bank.id == bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco no encontrado")
    return {
        "id": bank.id,
        "name": bank.name,
        "spread_multiplier": bank.spread_multiplier,
        "is_active": bank.is_active,
    }