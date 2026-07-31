from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.api.patients.repository import (
    count_encounters_by_patient,
    create_patient,
    delete_patient,
    find_patient_by_info,
    get_encounters_by_patient,
    get_patient_by_id,
    get_patients,
    update_patient,
)
from src.api.patients.schemas import PatientDetail, PatientEncounterCheck, PatientOut

if TYPE_CHECKING:
    from src.models.database import Patient


def _patient_to_out(p: "Patient") -> dict:
    return {
        "id": p.id,
        "full_name": p.full_name,
        "date_of_birth": p.date_of_birth,
        "gender": p.gender,
        "phone": p.phone,
        "email": p.email,
        "address": p.address,
        "medical_record_no": p.medical_record_no,
        "created_at": p.created_at.isoformat() if p.created_at else "",
        "updated_at": p.updated_at.isoformat() if p.updated_at else "",
    }


def get_patient_detail(db: Session, patient_id: int) -> PatientDetail:
    patient = get_patient_by_id(db, patient_id)
    base = _patient_to_out(patient)
    base["encounter_count"] = count_encounters_by_patient(db, patient_id)
    return PatientDetail(**base)


def get_patient_list(
    db: Session, page: int = 1, size: int = 20, search: str | None = None, doctor_id: int | None = None
) -> dict:
    skip = (page - 1) * size
    patients, total = get_patients(db, skip=skip, limit=size, search=search, doctor_id=doctor_id)
    return {
        "items": [PatientOut(**_patient_to_out(p)) for p in patients],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def create_new_patient(db: Session, data: dict) -> PatientOut:
    patient = create_patient(db, **data)
    return PatientOut(**_patient_to_out(patient))


def update_existing_patient(db: Session, patient_id: int, data: dict) -> PatientOut:
    patient = update_patient(db, patient_id, **data)
    return PatientOut(**_patient_to_out(patient))


def remove_patient(db: Session, patient_id: int) -> dict:
    delete_patient(db, patient_id)
    return {"message": "Xóa bệnh nhân thành công"}


def get_patient_encounter_history(
    db: Session, patient_id: int, page: int = 1, size: int = 20
) -> dict:
    get_patient_by_id(db, patient_id)
    skip = (page - 1) * size
    encounters, total = get_encounters_by_patient(db, patient_id, skip=skip, limit=size)
    items = []
    for e in encounters:
        items.append(
            {
                "id": e.id,
                "doctor_id": e.doctor_id,
                "doctor_name": e.doctor.full_name if e.doctor else "",
                "encounter_date": e.encounter_date,
                "chief_complaint": e.chief_complaint,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else "",
            }
        )
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def check_patient_visited(
    db: Session,
    full_name: str | None = None,
    date_of_birth: str | None = None,
    phone: str | None = None,
) -> PatientEncounterCheck | None:
    result = find_patient_by_info(db, full_name=full_name, date_of_birth=date_of_birth, phone=phone)
    if not result:
        return None
    return PatientEncounterCheck(
        patient=PatientOut(**_patient_to_out(result["patient"])),
        has_been_visited=result["has_been_visited"],
        encounter_count=result["encounter_count"],
        last_encounter=result["last_encounter"],
    )
