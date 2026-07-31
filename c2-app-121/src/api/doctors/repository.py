from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.exceptions import NotFoundError
from src.models.database import Doctor, Encounter, Shift


def get_doctor_by_id(db: Session, doctor_id: int) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise NotFoundError(resource="Bác sĩ")
    return doctor


def get_doctors(
    db: Session, skip: int = 0, limit: int = 20, is_active: bool | None = None
) -> tuple[list[Doctor], int]:
    query = db.query(Doctor)
    if is_active is not None:
        query = query.filter(Doctor.is_active == is_active)
    total = query.count()
    doctors = query.order_by(Doctor.full_name).offset(skip).limit(limit).all()
    return doctors, total


def create_doctor(db: Session, **kwargs) -> Doctor:
    doctor = Doctor(**kwargs)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def update_doctor(db: Session, doctor_id: int, **kwargs) -> Doctor:
    doctor = get_doctor_by_id(db, doctor_id)
    for key, value in kwargs.items():
        if value is not None:
            setattr(doctor, key, value)
    db.commit()
    db.refresh(doctor)
    return doctor


def delete_doctor(db: Session, doctor_id: int) -> bool:
    doctor = get_doctor_by_id(db, doctor_id)
    db.delete(doctor)
    db.commit()
    return True


def count_encounters_by_doctor(db: Session, doctor_id: int) -> int:
    return db.query(Encounter).filter(Encounter.doctor_id == doctor_id).count()


def count_completed_encounters(db: Session, doctor_id: int) -> int:
    return (
        db.query(Encounter)
        .filter(Encounter.doctor_id == doctor_id, Encounter.status == "completed")
        .count()
    )


def count_in_progress_encounters(db: Session, doctor_id: int) -> int:
    return (
        db.query(Encounter)
        .filter(Encounter.doctor_id == doctor_id, Encounter.status == "in_progress")
        .count()
    )


def count_patients_by_doctor(db: Session, doctor_id: int) -> int:
    return (
        db.query(func.count(func.distinct(Encounter.patient_id)))
        .filter(Encounter.doctor_id == doctor_id)
        .scalar()
        or 0
    )


def count_shifts_by_doctor(db: Session, doctor_id: int) -> int:
    return db.query(Shift).filter(Shift.doctor_id == doctor_id).count()
