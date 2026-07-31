from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.auth.dependencies import get_current_user
from src.api.deps import get_db
from src.api.shifts.schemas import ShiftCreate, ShiftList, ShiftOut, ShiftUpdate, ShiftWithDoctor
from src.api.shifts.service import (
    create_new_shift,
    get_shift_detail,
    get_shift_list,
    remove_shift,
    update_existing_shift,
)
from src.core.exceptions import ForbiddenError
from src.models.database import User, Doctor

router = APIRouter(prefix="/shifts", tags=["Shifts"])


def _resolve_doctor_id(user: User, db: Session) -> int | None:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    return doctor.id if doctor else None


@router.get("/", response_model=ShiftList)
async def list_shifts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    doctor_id: int | None = Query(None, description="Lọc theo bác sĩ"),
    shift_date: str | None = Query(None, description="Lọc theo ngày (YYYY-MM-DD)"),
    status: str | None = Query(None, description="Lọc theo trạng thái"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Danh sách ca trực (lọc theo bác sĩ, ngày, trạng thái)."""
    resolved_doctor_id = _resolve_doctor_id(user, db)
    if resolved_doctor_id is not None:
        doctor_id = resolved_doctor_id
    return get_shift_list(db, page=page, size=size, doctor_id=doctor_id, shift_date=shift_date, status=status)


@router.get("/{shift_id}", response_model=ShiftWithDoctor)
async def get_shift(
    shift_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftWithDoctor:
    """Chi tiết ca trực (kèm thông tin bác sĩ)."""
    resolved_doctor_id = _resolve_doctor_id(user, db)
    if resolved_doctor_id is not None:
        from src.api.shifts.repository import get_shift_by_id
        shift = get_shift_by_id(db, shift_id)
        if shift.doctor_id != resolved_doctor_id:
            raise ForbiddenError(detail="Bạn không có quyền truy cập ca trực này")
    return get_shift_detail(db, shift_id)


@router.post("/", response_model=ShiftOut, status_code=201)
async def create_shift(
    request: ShiftCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftOut:
    """Tạo ca trực mới."""
    return create_new_shift(db, request.model_dump())


@router.patch("/{shift_id}", response_model=ShiftOut)
async def update_shift(
    shift_id: int,
    request: ShiftUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShiftOut:
    """Cập nhật ca trực (trạng thái, giờ)."""
    return update_existing_shift(db, shift_id, request.model_dump(exclude_unset=True))


@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xóa ca trực."""
    return remove_shift(db, shift_id)
