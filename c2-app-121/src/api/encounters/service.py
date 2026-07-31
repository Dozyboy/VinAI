from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.api.encounters.repository import (
    create_encounter,
    create_or_update_assessment,
    create_or_update_diagnosis,
    create_or_update_objective,
    create_or_update_plan,
    create_or_update_subjective,
    create_soap_note,
    delete_encounter,
    get_encounter_by_id,
    get_encounters,
    get_soap_note_by_id,
    update_encounter,
)
from src.api.encounters.schemas import (
    DoctorBrief,
    EncounterDetail,
    EncounterListOut,
    PatientBrief,
    RecordingOut,
    SoapNoteCreatedOut,
    SoapNoteFullOut,
    TranscriptOut,
)

if TYPE_CHECKING:
    from src.models.database import SoapNote


def _build_soap_full(soap_note: "SoapNote") -> dict:
    result = {
        "id": soap_note.id,
        "note_type": soap_note.note_type,
        "created_at": soap_note.created_at.isoformat() if soap_note.created_at else "",
        "updated_at": soap_note.updated_at.isoformat() if soap_note.updated_at else "",
    }
    if soap_note.subjective:
        result["subjective"] = {
            "chief_complaint": soap_note.subjective.chief_complaint,
            "history": soap_note.subjective.history,
            "review_of_systems": soap_note.subjective.review_of_systems,
        }
    if soap_note.objective:
        result["objective"] = {
            "vital_signs": soap_note.objective.vital_signs,
            "physical_exam": soap_note.objective.physical_exam,
            "lab_results": soap_note.objective.lab_results,
        }
    if soap_note.assessment:
        result["assessment"] = {
            "diagnosis": soap_note.assessment.diagnosis,
            "severity": soap_note.assessment.severity,
            "notes": soap_note.assessment.notes,
        }
        if soap_note.assessment.diagnosis_detail:
            result["diagnosis"] = {
                "primary_diagnosis": soap_note.assessment.diagnosis_detail.primary_diagnosis,
                "differential_diagnoses": soap_note.assessment.diagnosis_detail.differential_diagnoses,
                "icd_code": soap_note.assessment.diagnosis_detail.icd_code,
            }
            if soap_note.assessment.diagnosis_detail.plan:
                result["plan"] = {
                    "treatment": soap_note.assessment.diagnosis_detail.plan.treatment,
                    "medications": soap_note.assessment.diagnosis_detail.plan.medications,
                    "follow_up": soap_note.assessment.diagnosis_detail.plan.follow_up,
                    "patient_education": soap_note.assessment.diagnosis_detail.plan.patient_education,
                }
    return result


def get_encounter_detail(db: Session, encounter_id: int) -> EncounterDetail:
    e = get_encounter_by_id(db, encounter_id)
    doctor = DoctorBrief(
        id=e.doctor.id,
        full_name=e.doctor.full_name,
        specialization=e.doctor.specialization,
        phone=e.doctor.phone,
        email=e.doctor.email,
    ) if e.doctor else None
    patient = PatientBrief(
        id=e.patient.id,
        full_name=e.patient.full_name,
        date_of_birth=e.patient.date_of_birth,
        gender=e.patient.gender,
        phone=e.patient.phone,
        medical_record_no=e.patient.medical_record_no,
    ) if e.patient else None
    recordings = [
        RecordingOut(
            id=r.id,
            file_name=r.file_name,
            file_path=r.file_path,
            duration_sec=r.duration_sec,
            file_size_bytes=r.file_size_bytes,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in (e.recordings or [])
    ]
    transcripts = [
        TranscriptOut(
            id=t.id,
            raw_transcript=t.raw_transcript,
            corrected_transcript=t.corrected_transcript,
            language=t.language,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else "",
        )
        for t in (e.transcripts or [])
    ]
    soap_notes = [SoapNoteFullOut(**_build_soap_full(sn)) for sn in (e.soap_notes or [])]
    return EncounterDetail(
        id=e.id,
        encounter_date=e.encounter_date,
        chief_complaint=e.chief_complaint,
        status=e.status,
        created_at=e.created_at.isoformat() if e.created_at else "",
        updated_at=e.updated_at.isoformat() if e.updated_at else "",
        doctor=doctor,
        patient=patient,
        recordings=recordings,
        transcripts=transcripts,
        soap_notes=soap_notes,
    )


def get_encounter_list(
    db: Session,
    page: int = 1,
    size: int = 20,
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    skip = (page - 1) * size
    encounters, total = get_encounters(
        db, skip=skip, limit=size, doctor_id=doctor_id, patient_id=patient_id,
        status=status, date_from=date_from, date_to=date_to,
    )
    items = []
    for e in encounters:
        items.append(
            EncounterListOut(
                id=e.id,
                doctor_id=e.doctor_id,
                doctor_name=e.doctor.full_name if e.doctor else "",
                patient_id=e.patient_id,
                patient_name=e.patient.full_name if e.patient else "",
                encounter_date=e.encounter_date,
                chief_complaint=e.chief_complaint,
                status=e.status,
                created_at=e.created_at.isoformat() if e.created_at else "",
            )
        )
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


def create_new_encounter(db: Session, data: dict) -> dict:
    shift_id = data.get("shift_id")
    doctor_id = data.get("doctor_id")

    if not shift_id and doctor_id:
        from datetime import datetime
        from src.models.database import Shift

        date_str = (data.get("encounter_date") or datetime.now().strftime("%Y-%m-%d %H:%M"))[:10]
        shift = (
            db.query(Shift)
            .filter(Shift.doctor_id == doctor_id, Shift.shift_date == date_str)
            .first()
        )
        if not shift:
            shift = Shift(
                doctor_id=doctor_id,
                shift_date=date_str,
                start_time="08:00",
                end_time="17:00",
                status="in_progress",
            )
            db.add(shift)
            db.flush()
        data["shift_id"] = shift.id

    encounter = create_encounter(db, **data)
    return {
        "id": encounter.id,
        "doctor_id": encounter.doctor_id,
        "patient_id": encounter.patient_id,
        "shift_id": encounter.shift_id,
        "encounter_date": encounter.encounter_date,
        "status": encounter.status,
        "message": "Tạo lượt khám thành công",
    }


def update_existing_encounter(db: Session, encounter_id: int, data: dict) -> dict:
    encounter = update_encounter(db, encounter_id, **data)
    return {
        "id": encounter.id,
        "status": encounter.status,
        "chief_complaint": encounter.chief_complaint,
        "message": "Cập nhật lượt khám thành công",
    }


def remove_encounter(db: Session, encounter_id: int) -> dict:
    delete_encounter(db, encounter_id)
    return {"message": "Xóa lượt khám thành công"}


# ── SOAP Note Service ──


def create_soap_note_for_encounter(db: Session, encounter_id: int, data: dict) -> SoapNoteCreatedOut:
    get_encounter_by_id(db, encounter_id)
    note = create_soap_note(db, encounter_id, note_type=data.get("note_type", "initial"))

    if data.get("subjective"):
        subj_data = {k: v for k, v in data["subjective"].items() if v}
        if subj_data:
            create_or_update_subjective(db, note.id, subj_data)

    if data.get("objective"):
        obj_data = {k: v for k, v in data["objective"].items() if v}
        if obj_data:
            create_or_update_objective(db, note.id, obj_data)

    if data.get("assessment"):
        asm_data = {k: v for k, v in data["assessment"].items() if v}
        if asm_data:
            assessment = create_or_update_assessment(db, note.id, asm_data)
            if data.get("diagnosis"):
                diag_data = {k: v for k, v in data["diagnosis"].items() if v}
                if diag_data:
                    diagnosis = create_or_update_diagnosis(db, assessment.id, diag_data)
                    if data.get("plan"):
                        plan_data = {k: v for k, v in data["plan"].items() if v}
                        if plan_data:
                            create_or_update_plan(db, diagnosis.id, plan_data)

    return SoapNoteCreatedOut(id=note.id, encounter_id=encounter_id, note_type=note.note_type)


def update_soap_subjective(db: Session, note_id: int, data: dict) -> dict:
    note = get_soap_note_by_id(db, note_id)
    clean = {k: v for k, v in data.items() if v is not None}
    create_or_update_subjective(db, note.id, clean)
    return {"message": "Cập nhật Subjective thành công", "note_id": note.id}


def update_soap_objective(db: Session, note_id: int, data: dict) -> dict:
    note = get_soap_note_by_id(db, note_id)
    clean = {k: v for k, v in data.items() if v is not None}
    create_or_update_objective(db, note.id, clean)
    return {"message": "Cập nhật Objective thành công", "note_id": note.id}


def update_soap_assessment(db: Session, note_id: int, data: dict) -> dict:
    note = get_soap_note_by_id(db, note_id)
    clean = {k: v for k, v in data.items() if v is not None}
    create_or_update_assessment(db, note.id, clean)
    return {"message": "Cập nhật Assessment thành công", "note_id": note.id}


def update_soap_diagnosis(db: Session, note_id: int, data: dict) -> dict:
    note = get_soap_note_by_id(db, note_id)
    clean = {k: v for k, v in data.items() if v is not None}
    if not note.assessment:
        assessment = create_or_update_assessment(db, note.id, {})
    else:
        assessment = note.assessment
    create_or_update_diagnosis(db, assessment.id, clean)
    return {"message": "Cập nhật Diagnosis thành công", "note_id": note.id}


def update_soap_plan(db: Session, note_id: int, data: dict) -> dict:
    note = get_soap_note_by_id(db, note_id)
    clean = {k: v for k, v in data.items() if v is not None}
    if not note.assessment:
        assessment = create_or_update_assessment(db, note.id, {})
    else:
        assessment = note.assessment
    if not assessment.diagnosis_detail:
        diagnosis = create_or_update_diagnosis(db, assessment.id, {})
    else:
        diagnosis = assessment.diagnosis_detail
    create_or_update_plan(db, diagnosis.id, clean)
    return {"message": "Cập nhật Plan thành công", "note_id": note.id}
