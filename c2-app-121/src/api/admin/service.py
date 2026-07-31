from sqlalchemy.orm import Session

from src.models.database import ClinicalNote, Doctor, Encounter, Patient, Shift, User


def get_admin_stats(db: Session) -> dict:
    return {
        "total_users": db.query(User).count(),
        "total_notes": db.query(ClinicalNote).count(),
        "active_users": db.query(User).filter(User.is_active).count(),
        "total_doctors": db.query(Doctor).count(),
        "total_patients": db.query(Patient).count(),
        "total_encounters": db.query(Encounter).count(),
        "total_shifts": db.query(Shift).count(),
        "completed_encounters": db.query(Encounter).filter(Encounter.status == "completed").count(),
    }
