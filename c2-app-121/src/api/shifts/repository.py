from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError
from src.models.database import Shift


def get_shift_by_id(db: Session, shift_id: int) -> Shift:
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise NotFoundError(resource="Ca trực")
    return shift


def get_shifts(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    doctor_id: int | None = None,
    shift_date: str | None = None,
    status: str | None = None,
) -> tuple[list[Shift], int]:
    query = db.query(Shift)
    if doctor_id is not None:
        query = query.filter(Shift.doctor_id == doctor_id)
    if shift_date is not None:
        query = query.filter(Shift.shift_date == shift_date)
    if status is not None:
        query = query.filter(Shift.status == status)
    total = query.count()
    shifts = query.order_by(Shift.shift_date.desc(), Shift.start_time).offset(skip).limit(limit).all()
    return shifts, total


def create_shift(db: Session, **kwargs) -> Shift:
    shift = Shift(**kwargs)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def update_shift(db: Session, shift_id: int, **kwargs) -> Shift:
    shift = get_shift_by_id(db, shift_id)
    for key, value in kwargs.items():
        if value is not None:
            setattr(shift, key, value)
    db.commit()
    db.refresh(shift)
    return shift


def delete_shift(db: Session, shift_id: int) -> bool:
    shift = get_shift_by_id(db, shift_id)
    db.delete(shift)
    db.commit()
    return True
