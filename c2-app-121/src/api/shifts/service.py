from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.api.shifts.repository import create_shift, delete_shift, get_shift_by_id, get_shifts, update_shift
from src.api.shifts.schemas import ShiftOut, ShiftWithDoctor

if TYPE_CHECKING:
    from src.models.database import Shift


def _shift_to_out(s: "Shift") -> dict:
    return {
        "id": s.id,
        "doctor_id": s.doctor_id,
        "shift_date": s.shift_date,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else "",
    }


def _shift_with_doctor(s: "Shift") -> dict:
    base = _shift_to_out(s)
    base["doctor_name"] = s.doctor.full_name if s.doctor else ""
    base["doctor_specialization"] = s.doctor.specialization if s.doctor else ""
    return base


def get_shift_detail(db: Session, shift_id: int) -> ShiftWithDoctor:
    shift = get_shift_by_id(db, shift_id)
    return ShiftWithDoctor(**_shift_with_doctor(shift))


def get_shift_list(
    db: Session,
    page: int = 1,
    size: int = 20,
    doctor_id: int | None = None,
    shift_date: str | None = None,
    status: str | None = None,
) -> dict:
    skip = (page - 1) * size
    shifts, total = get_shifts(db, skip=skip, limit=size, doctor_id=doctor_id, shift_date=shift_date, status=status)
    return {
        "items": [ShiftWithDoctor(** _shift_with_doctor(s)) for s in shifts],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def create_new_shift(db: Session, data: dict) -> ShiftOut:
    shift = create_shift(db, **data)
    return ShiftOut(**_shift_to_out(shift))


def update_existing_shift(db: Session, shift_id: int, data: dict) -> ShiftOut:
    shift = update_shift(db, shift_id, **data)
    return ShiftOut(**_shift_to_out(shift))


def remove_shift(db: Session, shift_id: int) -> dict:
    delete_shift(db, shift_id)
    return {"message": "Xóa ca trực thành công"}
