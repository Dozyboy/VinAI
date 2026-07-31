from sqlalchemy.orm import Session, joinedload

from src.core.exceptions import NotFoundError
from src.models.database import (
    Encounter,
    SoapAssessment,
    SoapDiagnosis,
    SoapNote,
    SoapObjective,
    SoapPlan,
    SoapSubjective,
)


def get_encounter_by_id(db: Session, encounter_id: int) -> Encounter:
    encounter = (
        db.query(Encounter)
        .options(
            joinedload(Encounter.doctor),
            joinedload(Encounter.patient),
            joinedload(Encounter.recordings),
            joinedload(Encounter.transcripts),
            joinedload(Encounter.soap_notes)
            .joinedload(SoapNote.subjective),
            joinedload(Encounter.soap_notes)
            .joinedload(SoapNote.objective),
            joinedload(Encounter.soap_notes)
            .joinedload(SoapNote.assessment)
            .joinedload(SoapAssessment.diagnosis_detail)
            .joinedload(SoapDiagnosis.plan),
        )
        .filter(Encounter.id == encounter_id)
        .first()
    )
    if not encounter:
        raise NotFoundError(resource="Lượt khám")
    return encounter


def get_encounters(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[Encounter], int]:
    query = db.query(Encounter).options(joinedload(Encounter.doctor), joinedload(Encounter.patient))
    if doctor_id is not None:
        query = query.filter(Encounter.doctor_id == doctor_id)
    if patient_id is not None:
        query = query.filter(Encounter.patient_id == patient_id)
    if status is not None:
        query = query.filter(Encounter.status == status)
    if date_from is not None:
        query = query.filter(Encounter.encounter_date >= date_from)
    if date_to is not None:
        query = query.filter(Encounter.encounter_date <= date_to)
    total = query.count()
    encounters = query.order_by(Encounter.encounter_date.desc()).offset(skip).limit(limit).all()
    return encounters, total


def create_encounter(db: Session, **kwargs) -> Encounter:
    encounter = Encounter(**kwargs)
    db.add(encounter)
    db.commit()
    db.refresh(encounter)
    return encounter


def update_encounter(db: Session, encounter_id: int, **kwargs) -> Encounter:
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        raise NotFoundError(resource="Lượt khám")
    for key, value in kwargs.items():
        if value is not None:
            setattr(encounter, key, value)
    db.commit()
    db.refresh(encounter)
    return encounter


def delete_encounter(db: Session, encounter_id: int) -> bool:
    encounter = db.query(Encounter).filter(Encounter.id == encounter_id).first()
    if not encounter:
        return False
    db.delete(encounter)
    db.commit()
    return True


# ── SOAP Note Repository ──


def get_soap_note_by_id(db: Session, note_id: int) -> SoapNote:
    note = (
        db.query(SoapNote)
        .options(
            joinedload(SoapNote.subjective),
            joinedload(SoapNote.objective),
            joinedload(SoapNote.assessment)
            .joinedload(SoapAssessment.diagnosis_detail)
            .joinedload(SoapDiagnosis.plan),
        )
        .filter(SoapNote.id == note_id)
        .first()
    )
    if not note:
        raise NotFoundError(resource="SOAP note")
    return note


def create_soap_note(db: Session, encounter_id: int, note_type: str = "initial") -> SoapNote:
    note = SoapNote(encounter_id=encounter_id, note_type=note_type)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def create_or_update_subjective(db: Session, soap_note_id: int, data: dict) -> SoapSubjective:
    existing = db.query(SoapSubjective).filter(SoapSubjective.soap_note_id == soap_note_id).first()
    if existing:
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    subj = SoapSubjective(soap_note_id=soap_note_id, **data)
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


def create_or_update_objective(db: Session, soap_note_id: int, data: dict) -> SoapObjective:
    existing = db.query(SoapObjective).filter(SoapObjective.soap_note_id == soap_note_id).first()
    if existing:
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    obj = SoapObjective(soap_note_id=soap_note_id, **data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_or_update_assessment(db: Session, soap_note_id: int, data: dict) -> SoapAssessment:
    existing = db.query(SoapAssessment).filter(SoapAssessment.soap_note_id == soap_note_id).first()
    if existing:
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    assessment = SoapAssessment(soap_note_id=soap_note_id, **data)
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def create_or_update_diagnosis(db: Session, soap_assessment_id: int, data: dict) -> SoapDiagnosis:
    existing = db.query(SoapDiagnosis).filter(SoapDiagnosis.soap_assessment_id == soap_assessment_id).first()
    if existing:
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    diagnosis = SoapDiagnosis(soap_assessment_id=soap_assessment_id, **data)
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)
    return diagnosis


def create_or_update_plan(db: Session, soap_diagnosis_id: int, data: dict) -> SoapPlan:
    existing = db.query(SoapPlan).filter(SoapPlan.soap_diagnosis_id == soap_diagnosis_id).first()
    if existing:
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    plan = SoapPlan(soap_diagnosis_id=soap_diagnosis_id, **data)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
