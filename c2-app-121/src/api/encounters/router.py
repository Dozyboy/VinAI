from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.auth.dependencies import get_current_user
from src.api.deps import get_db
from src.api.encounters.schemas import (
    AssessmentUpdate,
    DiagnosisUpdate,
    EncounterCreate,
    EncounterDetail,
    EncounterList,
    EncounterUpdate,
    ObjectiveUpdate,
    PlanUpdate,
    SoapNoteCreate,
    SoapNoteCreatedOut,
    SubjectiveUpdate,
)
from src.api.encounters.service import (
    create_new_encounter,
    create_soap_note_for_encounter,
    get_encounter_detail,
    get_encounter_list,
    remove_encounter,
    update_existing_encounter,
    update_soap_assessment,
    update_soap_diagnosis,
    update_soap_objective,
    update_soap_plan,
    update_soap_subjective,
)
from src.core.exceptions import ForbiddenError
from src.models.database import User, Doctor

router = APIRouter(prefix="/encounters", tags=["Encounters"])


def _resolve_doctor_id(user: User, db: Session) -> int | None:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    return doctor.id if doctor else None


def _require_own_encounter(doctor_id: int | None, encounter_id: int, db: Session) -> None:
    if doctor_id is None:
        return
    from src.api.encounters.repository import get_encounter_by_id
    encounter = get_encounter_by_id(db, encounter_id)
    if encounter.doctor_id != doctor_id:
        raise ForbiddenError(detail="Bạn không có quyền truy cập lượt khám này")


@router.get("/", response_model=EncounterList)
async def list_encounters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    doctor_id: int | None = Query(None, description="Lọc theo bác sĩ"),
    patient_id: int | None = Query(None, description="Lọc theo bệnh nhân"),
    status: str | None = Query(None, description="Lọc theo trạng thái"),
    date_from: str | None = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Đến ngày (YYYY-MM-DD)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Danh sách lượt khám (lọc theo bác sĩ, BN, ngày, trạng thái)."""
    resolved_doctor_id = _resolve_doctor_id(user, db)
    if resolved_doctor_id is not None:
        doctor_id = resolved_doctor_id
    return get_encounter_list(
        db, page=page, size=size, doctor_id=doctor_id, patient_id=patient_id,
        status=status, date_from=date_from, date_to=date_to,
    )


@router.get("/{encounter_id}", response_model=EncounterDetail)
async def get_encounter(
    encounter_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EncounterDetail:
    """Chi tiết lượt khám: bác sĩ, BN, recordings, transcripts, full SOAP (S/O/A/D/P)."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return get_encounter_detail(db, encounter_id)


@router.post("/", status_code=201)
async def create_encounter(
    request: EncounterCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Tạo lượt khám mới."""
    return create_new_encounter(db, request.model_dump())


@router.put("/{encounter_id}")
async def update_encounter(
    encounter_id: int,
    request: EncounterUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Cập nhật lượt khám (chief_complaint, status)."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return update_existing_encounter(db, encounter_id, request.model_dump(exclude_unset=True))


@router.delete("/{encounter_id}")
async def delete_encounter(
    encounter_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Xóa lượt khám."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return remove_encounter(db, encounter_id)


# ───── SOAP Note nested endpoints ─────


@router.post("/{encounter_id}/soap-notes", response_model=SoapNoteCreatedOut, status_code=201)
async def create_soap_note(
    encounter_id: int,
    request: SoapNoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SoapNoteCreatedOut:
    """Tạo SOAP note mới cho encounter (kèm S/O/A/D/P)."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return create_soap_note_for_encounter(db, encounter_id, request.model_dump())


@router.put("/{encounter_id}/soap-notes/{note_id}/subjective")
async def update_subjective(
    encounter_id: int,
    note_id: int,
    request: SubjectiveUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Chỉnh sửa phần Subjective (S) của SOAP note."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return update_soap_subjective(db, note_id, request.model_dump(exclude_unset=True))


@router.put("/{encounter_id}/soap-notes/{note_id}/objective")
async def update_objective(
    encounter_id: int,
    note_id: int,
    request: ObjectiveUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Chỉnh sửa phần Objective (O) của SOAP note."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return update_soap_objective(db, note_id, request.model_dump(exclude_unset=True))


@router.put("/{encounter_id}/soap-notes/{note_id}/assessment")
async def update_assessment(
    encounter_id: int,
    note_id: int,
    request: AssessmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Chỉnh sửa phần Assessment (A) của SOAP note."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return update_soap_assessment(db, note_id, request.model_dump(exclude_unset=True))


@router.put("/{encounter_id}/soap-notes/{note_id}/diagnosis")
async def update_diagnosis(
    encounter_id: int,
    note_id: int,
    request: DiagnosisUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Chỉnh sửa phần Diagnosis (D) của SOAP note."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return update_soap_diagnosis(db, note_id, request.model_dump(exclude_unset=True))


@router.put("/{encounter_id}/soap-notes/{note_id}/plan")
async def update_plan(
    encounter_id: int,
    note_id: int,
    request: PlanUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Chỉnh sửa phần Plan (P) của SOAP note."""
    doctor_id = _resolve_doctor_id(user, db)
    _require_own_encounter(doctor_id, encounter_id, db)
    return update_soap_plan(db, note_id, request.model_dump(exclude_unset=True))
