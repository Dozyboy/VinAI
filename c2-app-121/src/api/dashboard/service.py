from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from src.models.database import Doctor, Encounter, Patient, Recording, Shift, SoapAssessment, SoapDiagnosis, SoapNote


def get_dashboard_summary(db: Session, doctor_id: int | None = None) -> dict:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    enc_query = db.query(Encounter)
    if doctor_id is not None:
        enc_query = enc_query.filter(Encounter.doctor_id == doctor_id)
    return {
        "total_doctors": db.query(Doctor).filter(Doctor.is_active).count(),
        "total_patients": db.query(Patient).count(),
        "total_encounters": enc_query.count(),
        "completed_encounters": enc_query.filter(Encounter.status == "completed").count(),
        "in_progress_encounters": enc_query.filter(Encounter.status == "in_progress").count(),
        "today_encounters": enc_query.filter(Encounter.encounter_date >= today).count(),
        "total_recordings": db.query(Recording).count(),
    }


def get_doctor_workload(db: Session) -> list[dict]:
    results = (
        db.query(
            Doctor.id,
            Doctor.full_name,
            Doctor.specialization,
            func.count(func.distinct(Encounter.id)).label("encounter_count"),
            func.count(func.distinct(Encounter.patient_id)).label("patient_count"),
        )
        .outerjoin(Encounter, Encounter.doctor_id == Doctor.id)
        .filter(Doctor.is_active)
        .group_by(Doctor.id)
        .order_by(func.count(Encounter.id).desc())
        .all()
    )
    return [
        {
            "doctor_id": r.id,
            "doctor_name": r.full_name,
            "specialization": r.specialization,
            "encounter_count": r.encounter_count,
            "patient_count": r.patient_count,
        }
        for r in results
    ]


def get_top_diagnoses(db: Session, limit: int = 10, doctor_id: int | None = None) -> list[dict]:
    query = (
        db.query(
            SoapDiagnosis.primary_diagnosis,
            func.count(SoapDiagnosis.id).label("count"),
        )
        .join(SoapAssessment, SoapAssessment.id == SoapDiagnosis.soap_assessment_id)
        .join(SoapNote, SoapNote.id == SoapAssessment.soap_note_id)
        .join(Encounter, Encounter.id == SoapNote.encounter_id)
        .filter(SoapDiagnosis.primary_diagnosis != "")
    )
    if doctor_id is not None:
        query = query.filter(Encounter.doctor_id == doctor_id)
    results = (
        query
        .group_by(SoapDiagnosis.primary_diagnosis)
        .order_by(func.count(SoapDiagnosis.id).desc())
        .limit(limit)
        .all()
    )
    return [{"diagnosis": r.primary_diagnosis, "count": r.count} for r in results]


def get_monthly_trend(db: Session, months: int = 6, doctor_id: int | None = None) -> list[dict]:
    query = db.query(
        func.substr(Encounter.encounter_date, 1, 7).label("month"),
        func.count(Encounter.id).label("count"),
    )
    if doctor_id is not None:
        query = query.filter(Encounter.doctor_id == doctor_id)
    results = (
        query
        .group_by(func.substr(Encounter.encounter_date, 1, 7))
        .order_by(func.substr(Encounter.encounter_date, 1, 7).desc())
        .limit(months)
        .all()
    )
    return [{"month": r.month, "count": r.count} for r in reversed(results)]


def get_daily_view(db: Session, date: str, doctor_id: int | None = None) -> dict:
    query = db.query(Shift).options(joinedload(Shift.doctor)).filter(Shift.shift_date == date)
    if doctor_id is not None:
        query = query.filter(Shift.doctor_id == doctor_id)
    shifts = query.order_by(Shift.start_time).all()

    shift_ids = [s.id for s in shifts]

    encounters_by_shift: dict[int, list] = {}
    if shift_ids:
        enc_query = db.query(Encounter).options(joinedload(Encounter.patient)).filter(Encounter.shift_id.in_(shift_ids))
        if doctor_id is not None:
            enc_query = enc_query.filter(Encounter.doctor_id == doctor_id)
        enc_rows = enc_query.order_by(Encounter.encounter_date).all()
        for e in enc_rows:
            encounters_by_shift.setdefault(e.shift_id, []).append(e)

    shift_items = []
    for s in shifts:
        enc_list = []
        for e in encounters_by_shift.get(s.id, []):
            enc_list.append({
                "id": e.id,
                "patient_id": e.patient_id,
                "patient_name": e.patient.full_name if e.patient else "",
                "chief_complaint": e.chief_complaint,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else "",
            })
        shift_items.append({
            "id": s.id,
            "doctor_id": s.doctor_id,
            "doctor_name": s.doctor.full_name if s.doctor else "",
            "specialization": s.doctor.specialization if s.doctor else "",
            "start_time": s.start_time,
            "end_time": s.end_time,
            "status": s.status,
            "encounters": enc_list,
            "encounter_count": len(enc_list),
        })

    unassigned = (
        db.query(Encounter)
        .options(joinedload(Encounter.patient))
        .filter(
            Encounter.encounter_date.like(f"{date}%"),
            (Encounter.shift_id.is_(None)) | (Encounter.shift_id == 0),
        )
    )
    if doctor_id is not None:
        unassigned = unassigned.filter(Encounter.doctor_id == doctor_id)
    unassigned = unassigned.order_by(Encounter.encounter_date).all()

    unassigned_items = [
        {
            "id": e.id,
            "patient_id": e.patient_id,
            "patient_name": e.patient.full_name if e.patient else "",
            "chief_complaint": e.chief_complaint,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in unassigned
    ]

    return {
        "date": date,
        "shifts": shift_items,
        "unassigned_encounters": unassigned_items,
    }
