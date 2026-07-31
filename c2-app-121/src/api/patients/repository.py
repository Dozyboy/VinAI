from sqlalchemy.orm import Session, joinedload

from src.core.exceptions import NotFoundError
from src.models.database import (
    Doctor,
    Encounter,
    Patient,
    SoapAssessment,
    SoapDiagnosis,
    SoapNote,
    SoapPlan,
)


def get_patient_by_id(db: Session, patient_id: int) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise NotFoundError(resource="Bệnh nhân")
    return patient


def get_patients(
    db: Session, skip: int = 0, limit: int = 20, search: str | None = None, doctor_id: int | None = None,
) -> tuple[list[Patient], int]:
    query = db.query(Patient)
    if doctor_id is not None:
        patient_ids_q = (
            db.query(Encounter.patient_id)
            .filter(Encounter.doctor_id == doctor_id)
            .distinct()
        )
        query = query.filter(Patient.id.in_(patient_ids_q))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            Patient.full_name.ilike(pattern) | Patient.phone.ilike(pattern) | Patient.medical_record_no.ilike(pattern)
        )
    total = query.count()
    patients = query.order_by(Patient.full_name).offset(skip).limit(limit).all()
    return patients, total


def create_patient(db: Session, **kwargs) -> Patient:
    patient = Patient(**kwargs)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient_id: int, **kwargs) -> Patient:
    patient = get_patient_by_id(db, patient_id)
    for key, value in kwargs.items():
        if value is not None:
            setattr(patient, key, value)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient_id: int) -> bool:
    patient = get_patient_by_id(db, patient_id)
    db.delete(patient)
    db.commit()
    return True


def count_encounters_by_patient(db: Session, patient_id: int) -> int:
    return db.query(Encounter).filter(Encounter.patient_id == patient_id).count()


def doctor_has_encounter_with_patient(db: Session, doctor_id: int, patient_id: int) -> bool:
    return db.query(Encounter).filter(
        Encounter.doctor_id == doctor_id, Encounter.patient_id == patient_id
    ).first() is not None


def get_encounters_by_patient(
    db: Session, patient_id: int, skip: int = 0, limit: int = 20
) -> tuple[list[Encounter], int]:
    total = db.query(Encounter).filter(Encounter.patient_id == patient_id).count()
    encounters = (
        db.query(Encounter)
        .filter(Encounter.patient_id == patient_id)
        .order_by(Encounter.encounter_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return encounters, total


def find_patient_by_info(
    db: Session,
    full_name: str | None = None,
    date_of_birth: str | None = None,
    phone: str | None = None,
) -> dict | None:
    query = db.query(Patient)
    if full_name:
        query = query.filter(Patient.full_name.ilike(f"%{full_name}%"))
    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth)
    if phone:
        query = query.filter(Patient.phone.ilike(f"%{phone}%"))

    patient = query.first()
    if not patient:
        return None

    encounter_count = db.query(Encounter).filter(Encounter.patient_id == patient.id).count()

    last_encounter = (
        db.query(Encounter)
        .options(
            joinedload(Encounter.doctor),
            joinedload(Encounter.soap_notes)
            .joinedload(SoapNote.subjective),
            joinedload(Encounter.soap_notes)
            .joinedload(SoapNote.objective),
            joinedload(Encounter.soap_notes)
            .joinedload(SoapNote.assessment)
            .joinedload(SoapAssessment.diagnosis_detail)
            .joinedload(SoapDiagnosis.plan),
        )
        .filter(Encounter.patient_id == patient.id)
        .order_by(Encounter.encounter_date.desc())
        .first()
    )

    last_encounter_info = None
    if last_encounter:
        soap_data = None
        if last_encounter.soap_notes:
            soap = last_encounter.soap_notes[0]
            soap_data = _build_soap_data(soap)

        last_encounter_info = {
            "id": last_encounter.id,
            "encounter_date": last_encounter.encounter_date,
            "status": last_encounter.status,
            "chief_complaint": last_encounter.chief_complaint,
            "doctor_name": last_encounter.doctor.full_name if last_encounter.doctor else None,
            "soap_note": soap_data,
        }

    return {
        "patient": patient,
        "has_been_visited": encounter_count > 0,
        "encounter_count": encounter_count,
        "last_encounter": last_encounter_info,
    }


def _build_soap_data(soap: SoapNote) -> dict:
    data = {"id": soap.id, "note_type": soap.note_type}

    if soap.subjective:
        data["subjective"] = {
            "chief_complaint": soap.subjective.chief_complaint,
            "history": soap.subjective.history,
            "review_of_systems": soap.subjective.review_of_systems,
        }

    if soap.objective:
        data["objective"] = {
            "vital_signs": soap.objective.vital_signs,
            "physical_exam": soap.objective.physical_exam,
            "lab_results": soap.objective.lab_results,
        }

    if soap.assessment:
        assessment_data = {
            "diagnosis": soap.assessment.diagnosis,
            "severity": soap.assessment.severity,
            "notes": soap.assessment.notes,
        }
        if soap.assessment.diagnosis_detail:
            diagnosis_detail = soap.assessment.diagnosis_detail
            assessment_data["diagnosis_detail"] = {
                "primary_diagnosis": diagnosis_detail.primary_diagnosis,
                "differential_diagnoses": diagnosis_detail.differential_diagnoses,
                "icd_code": diagnosis_detail.icd_code,
            }
            if diagnosis_detail.plan:
                assessment_data["diagnosis_detail"]["plan"] = {
                    "treatment": diagnosis_detail.plan.treatment,
                    "medications": diagnosis_detail.plan.medications,
                    "follow_up": diagnosis_detail.plan.follow_up,
                    "patient_education": diagnosis_detail.plan.patient_education,
                }
        data["assessment"] = assessment_data

    return data
