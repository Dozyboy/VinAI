from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.api.doctors.repository import (
    count_completed_encounters,
    count_encounters_by_doctor,
    count_in_progress_encounters,
    count_patients_by_doctor,
    count_shifts_by_doctor,
    create_doctor,
    delete_doctor,
    get_doctor_by_id,
    get_doctors,
    update_doctor,
)
from src.api.doctors.schemas import DoctorDetail, DoctorOut, DoctorStats

if TYPE_CHECKING:
    from src.models.database import Doctor


def _doctor_to_out(d: "Doctor") -> dict:
    return {
        "id": d.id,
        "full_name": d.full_name,
        "specialization": d.specialization,
        "email": d.email,
        "phone": d.phone,
        "is_active": d.is_active,
        "created_at": d.created_at.isoformat() if d.created_at else "",
        "updated_at": d.updated_at.isoformat() if d.updated_at else "",
    }


def get_doctor_detail(db: Session, doctor_id: int) -> DoctorDetail:
    doctor = get_doctor_by_id(db, doctor_id)
    base = _doctor_to_out(doctor)
    base["shift_count"] = count_shifts_by_doctor(db, doctor_id)
    base["encounter_count"] = count_encounters_by_doctor(db, doctor_id)
    base["patient_count"] = count_patients_by_doctor(db, doctor_id)
    return DoctorDetail(**base)


def get_doctor_list(
    db: Session, page: int = 1, size: int = 20, is_active: bool | None = None
) -> dict:
    skip = (page - 1) * size
    doctors, total = get_doctors(db, skip=skip, limit=size, is_active=is_active)
    return {
        "items": [DoctorOut(**_doctor_to_out(d)) for d in doctors],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def create_new_doctor(db: Session, data: dict) -> DoctorOut:
    doctor = create_doctor(db, **data)
    return DoctorOut(**_doctor_to_out(doctor))


def update_existing_doctor(db: Session, doctor_id: int, data: dict) -> DoctorOut:
    doctor = update_doctor(db, doctor_id, **data)
    return DoctorOut(**_doctor_to_out(doctor))


def remove_doctor(db: Session, doctor_id: int) -> dict:
    delete_doctor(db, doctor_id)
    return {"message": "Xóa bác sĩ thành công"}


def get_doctor_stats(db: Session, doctor_id: int) -> DoctorStats:
    get_doctor_by_id(db, doctor_id)
    return DoctorStats(
        total_encounters=count_encounters_by_doctor(db, doctor_id),
        completed_encounters=count_completed_encounters(db, doctor_id),
        in_progress_encounters=count_in_progress_encounters(db, doctor_id),
        total_patients=count_patients_by_doctor(db, doctor_id),
        total_shifts=count_shifts_by_doctor(db, doctor_id),
    )
