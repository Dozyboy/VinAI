from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.auth.dependencies import get_current_user
from src.api.deps import get_db
from src.api.patients.repository import doctor_has_encounter_with_patient
from src.api.patients.schemas import (
    PatientCreate,
    PatientDetail,
    PatientEncounterCheck,
    PatientList,
    PatientOut,
    PatientUpdate,
)
from src.api.patients.service import (
    check_patient_visited,
    create_new_patient,
    get_patient_detail,
    get_patient_encounter_history,
    get_patient_list,
    remove_patient,
    update_existing_patient,
)
from src.core.exceptions import ForbiddenError
from src.models.database import User, Doctor

router = APIRouter(prefix="/patients", tags=["Patients"])


def _resolve_doctor_id(user: User, db: Session) -> int | None:
    """Map User -> Doctor id bằng user_id FK. Trả None nếu không tìm thấy."""
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    return doctor.id if doctor else None


def _require_doctor_own_patient(doctor_id: int | None, patient_id: int, db: Session) -> None:
    """Kiểm tra bác sĩ có encounter với bệnh nhân này không."""
    if doctor_id is None:
        return
    if not doctor_has_encounter_with_patient(db, doctor_id, patient_id):
        raise ForbiddenError(detail="Bạn không có quyền truy cập bệnh nhân này")


@router.get("/", response_model=PatientList)
async def list_patients(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Tìm kiếm theo tên, SĐT, Mã BN"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Danh sách bệnh nhân (tìm kiếm theo tên/SĐT/mã BN)."""
    doctor_id = _resolve_doctor_id(user, db)
    return get_patient_list(db, page=page, size=size, search=search, doctor_id=doctor_id)


@router.get("/{patient_id}", response_model=PatientDetail)
async def get_patient(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientDetail:
    """Chi tiết bệnh nhân + số lượt khám."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_doctor_own_patient(doctor_id, patient_id, db)
    return get_patient_detail(db, patient_id)


@router.get("/{patient_id}/encounters")
async def get_patient_encounters(
    patient_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Lịch sử khám bệnh của bệnh nhân (kèm tên bác sĩ)."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_doctor_own_patient(doctor_id, patient_id, db)
    return get_patient_encounter_history(db, patient_id, page=page, size=size)


@router.get("/check-visited/", response_model=PatientEncounterCheck | None)
async def check_visited(
    full_name: str | None = Query(None, description="Tên bệnh nhân"),
    date_of_birth: str | None = Query(None, description="Ngày sinh (YYYY-MM-DD)"),
    phone: str | None = Query(None, description="Số điện thoại"),
    db: Session = Depends(get_db),
) -> PatientEncounterCheck | None:
    """Kiểm tra bệnh nhân đã khám chưa theo tên, ngày sinh, SĐT."""
    return check_patient_visited(db, full_name=full_name, date_of_birth=date_of_birth, phone=phone)


@router.post("/", response_model=PatientOut, status_code=201)
async def create_patient(
    request: PatientCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientOut:
    """Thêm bệnh nhân mới."""
    return create_new_patient(db, request.model_dump())


@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: int,
    request: PatientUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PatientOut:
    """Cập nhật thông tin bệnh nhân."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_doctor_own_patient(doctor_id, patient_id, db)
    return update_existing_patient(db, patient_id, request.model_dump(exclude_unset=True))


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xóa bệnh nhân."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_doctor_own_patient(doctor_id, patient_id, db)
    return remove_patient(db, patient_id)
