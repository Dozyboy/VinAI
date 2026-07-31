from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.base import Base, TimestampMixin


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ──────────────────────────────────────────────
#  Auth models (existing)
# ──────────────────────────────────────────────


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    clinical_notes: Mapped[list["ClinicalNote"]] = relationship(back_populates="user")
    doctor: Mapped["Doctor | None"] = relationship(back_populates="user")


class ClinicalNote(Base, TimestampMixin):
    __tablename__ = "clinical_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_transcript: Mapped[str] = mapped_column(Text, nullable=False, default="")
    soap_note: Mapped[str] = mapped_column(Text, nullable=False)
    audio_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship(back_populates="clinical_notes")


# ──────────────────────────────────────────────
#  Doctor flow models
# ──────────────────────────────────────────────


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="doctor")
    shifts: Mapped[list["Shift"]] = relationship(back_populates="doctor")
    encounters: Mapped[list["Encounter"]] = relationship(back_populates="doctor")


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    shift_date: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    doctor: Mapped["Doctor"] = relationship(back_populates="shifts")
    encounters: Mapped[list["Encounter"]] = relationship(back_populates="shift")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    medical_record_no: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    encounters: Mapped[list["Encounter"]] = relationship(back_populates="patient")


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    shift_id: Mapped[int | None] = mapped_column(ForeignKey("shifts.id"), nullable=True)
    encounter_date: Mapped[str] = mapped_column(String(30), nullable=False)
    chief_complaint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="in_progress", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    doctor: Mapped["Doctor"] = relationship(back_populates="encounters")
    patient: Mapped["Patient"] = relationship(back_populates="encounters")
    shift: Mapped["Shift | None"] = relationship(back_populates="encounters")
    recordings: Mapped[list["Recording"]] = relationship(back_populates="encounter")
    transcripts: Mapped[list["Transcript"]] = relationship(back_populates="encounter")
    soap_notes: Mapped[list["SoapNote"]] = relationship(back_populates="encounter")


class Recording(Base):
    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_sec: Mapped[int | None] = mapped_column(nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    encounter: Mapped["Encounter"] = relationship(back_populates="recordings")


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"), nullable=False)
    raw_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    corrected_transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="vi", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    encounter: Mapped["Encounter"] = relationship(back_populates="transcripts")


class SoapNote(Base):
    __tablename__ = "soap_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    encounter_id: Mapped[int] = mapped_column(ForeignKey("encounters.id"), nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), default="initial", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    encounter: Mapped["Encounter"] = relationship(back_populates="soap_notes")
    subjective: Mapped["SoapSubjective | None"] = relationship(back_populates="soap_note", uselist=False)
    objective: Mapped["SoapObjective | None"] = relationship(back_populates="soap_note", uselist=False)
    assessment: Mapped["SoapAssessment | None"] = relationship(back_populates="soap_note", uselist=False)


class SoapSubjective(Base):
    __tablename__ = "soap_subjective"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    soap_note_id: Mapped[int] = mapped_column(ForeignKey("soap_notes.id"), unique=True, nullable=False)
    chief_complaint: Mapped[str] = mapped_column(Text, default="", nullable=False)
    history: Mapped[str] = mapped_column(Text, default="", nullable=False)
    review_of_systems: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    soap_note: Mapped["SoapNote"] = relationship(back_populates="subjective")


class SoapObjective(Base):
    __tablename__ = "soap_objective"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    soap_note_id: Mapped[int] = mapped_column(ForeignKey("soap_notes.id"), unique=True, nullable=False)
    vital_signs: Mapped[str] = mapped_column(Text, default="", nullable=False)
    physical_exam: Mapped[str] = mapped_column(Text, default="", nullable=False)
    lab_results: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    soap_note: Mapped["SoapNote"] = relationship(back_populates="objective")


class SoapAssessment(Base):
    __tablename__ = "soap_assessment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    soap_note_id: Mapped[int] = mapped_column(ForeignKey("soap_notes.id"), unique=True, nullable=False)
    diagnosis: Mapped[str] = mapped_column(Text, default="", nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    soap_note: Mapped["SoapNote"] = relationship(back_populates="assessment")
    diagnosis_detail: Mapped["SoapDiagnosis | None"] = relationship(back_populates="assessment", uselist=False)


class SoapDiagnosis(Base):
    __tablename__ = "soap_diagnosis"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    soap_assessment_id: Mapped[int] = mapped_column(ForeignKey("soap_assessment.id"), unique=True, nullable=False)
    primary_diagnosis: Mapped[str] = mapped_column(Text, default="", nullable=False)
    differential_diagnoses: Mapped[str] = mapped_column(Text, default="", nullable=False)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    assessment: Mapped["SoapAssessment"] = relationship(back_populates="diagnosis_detail")
    plan: Mapped["SoapPlan | None"] = relationship(back_populates="diagnosis", uselist=False)


class SoapPlan(Base):
    __tablename__ = "soap_plan"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    soap_diagnosis_id: Mapped[int] = mapped_column(ForeignKey("soap_diagnosis.id"), unique=True, nullable=False)
    treatment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    medications: Mapped[str] = mapped_column(Text, default="", nullable=False)
    follow_up: Mapped[str] = mapped_column(Text, default="", nullable=False)
    patient_education: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    diagnosis: Mapped["SoapDiagnosis"] = relationship(back_populates="plan")
