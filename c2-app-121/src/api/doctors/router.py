from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.auth.dependencies import get_current_user
from src.api.deps import get_db
from src.api.doctors.schemas import DoctorCreate, DoctorDetail, DoctorList, DoctorOut, DoctorStats, DoctorUpdate
from src.api.doctors.service import (
    create_new_doctor,
    get_doctor_detail,
    get_doctor_list,
    get_doctor_stats,
    remove_doctor,
    update_existing_doctor,
)
from src.models.database import User

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("/", response_model=DoctorList)
async def list_doctors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Danh sách bác sĩ (có lọc theo trạng thái)."""
    return get_doctor_list(db, page=page, size=size, is_active=is_active)


@router.get("/{doctor_id}", response_model=DoctorDetail)
async def get_doctor(
    doctor_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DoctorDetail:
    """Chi tiết bác sĩ + số ca, số bệnh nhân, số ca."""
    return get_doctor_detail(db, doctor_id)


@router.get("/{doctor_id}/stats", response_model=DoctorStats)
async def get_doctor_statistics(
    doctor_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DoctorStats:
    """Thống kê của bác sĩ: tổng ca, bệnh nhân, ca trực."""
    return get_doctor_stats(db, doctor_id)


@router.post("/", response_model=DoctorOut, status_code=201)
async def create_doctor(
    request: DoctorCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DoctorOut:
    """Thêm bác sĩ mới."""
    return create_new_doctor(db, request.model_dump())


@router.put("/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    request: DoctorUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DoctorOut:
    """Cập nhật thông tin bác sĩ."""
    return update_existing_doctor(db, doctor_id, request.model_dump(exclude_unset=True))


@router.delete("/{doctor_id}")
async def delete_doctor(
    doctor_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xóa bác sĩ."""
    return remove_doctor(db, doctor_id)
