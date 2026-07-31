from pydantic import BaseModel, Field


class EncounterOut(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    encounter_date: str
    chief_complaint: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class EncounterListOut(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str = ""
    patient_id: int
    patient_name: str = ""
    encounter_date: str
    chief_complaint: str
    status: str
    created_at: str


class EncounterCreate(BaseModel):
    doctor_id: int = Field(..., ge=1)
    patient_id: int = Field(..., ge=1)
    shift_id: int | None = Field(default=None, description="Ca trực liên quan")
    encounter_date: str = Field(..., description="YYYY-MM-DD HH:MM")
    chief_complaint: str = Field(default="")
    status: str = Field(default="in_progress", pattern=r"^(in_progress|completed|cancelled)$")


class EncounterUpdate(BaseModel):
    chief_complaint: str | None = None
    status: str | None = Field(default=None, pattern=r"^(in_progress|completed|cancelled)$")


class EncounterList(BaseModel):
    items: list[EncounterListOut]
    total: int
    page: int
    size: int
    pages: int


class DoctorBrief(BaseModel):
    id: int
    full_name: str
    specialization: str
    phone: str | None = None
    email: str | None = None


class PatientBrief(BaseModel):
    id: int
    full_name: str
    date_of_birth: str | None = None
    gender: str | None = None
    phone: str | None = None
    medical_record_no: str | None = None


class SubjectiveOut(BaseModel):
    chief_complaint: str = ""
    history: str = ""
    review_of_systems: str = ""


class ObjectiveOut(BaseModel):
    vital_signs: str = ""
    physical_exam: str = ""
    lab_results: str = ""


class AssessmentOut(BaseModel):
    diagnosis: str = ""
    severity: str = ""
    notes: str = ""


class DiagnosisOut(BaseModel):
    primary_diagnosis: str = ""
    differential_diagnoses: str = ""
    icd_code: str | None = None


class PlanOut(BaseModel):
    treatment: str = ""
    medications: str = ""
    follow_up: str = ""
    patient_education: str = ""


class SoapNoteFullOut(BaseModel):
    id: int
    note_type: str
    created_at: str
    updated_at: str
    subjective: SubjectiveOut | None = None
    objective: ObjectiveOut | None = None
    assessment: AssessmentOut | None = None
    diagnosis: DiagnosisOut | None = None
    plan: PlanOut | None = None


class RecordingOut(BaseModel):
    id: int
    file_name: str
    file_path: str
    duration_sec: int | None = None
    file_size_bytes: int | None = None
    created_at: str

    model_config = {"from_attributes": True}


class TranscriptOut(BaseModel):
    id: int
    raw_transcript: str
    corrected_transcript: str
    language: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class EncounterDetail(BaseModel):
    id: int
    encounter_date: str
    chief_complaint: str
    status: str
    created_at: str
    updated_at: str
    doctor: DoctorBrief | None = None
    patient: PatientBrief | None = None
    recordings: list[RecordingOut] = []
    transcripts: list[TranscriptOut] = []
    soap_notes: list[SoapNoteFullOut] = []


# ── SOAP Note Write Schemas ──

class SoapNoteCreate(BaseModel):
    note_type: str = Field(default="initial", pattern=r"^(initial|follow_up|update)$")
    subjective: SubjectiveOut = Field(default_factory=SubjectiveOut)
    objective: ObjectiveOut = Field(default_factory=ObjectiveOut)
    assessment: AssessmentOut = Field(default_factory=AssessmentOut)
    diagnosis: DiagnosisOut = Field(default_factory=DiagnosisOut)
    plan: PlanOut = Field(default_factory=PlanOut)


class SubjectiveUpdate(BaseModel):
    chief_complaint: str | None = None
    history: str | None = None
    review_of_systems: str | None = None


class ObjectiveUpdate(BaseModel):
    vital_signs: str | None = None
    physical_exam: str | None = None
    lab_results: str | None = None


class AssessmentUpdate(BaseModel):
    diagnosis: str | None = None
    severity: str | None = None
    notes: str | None = None


class DiagnosisUpdate(BaseModel):
    primary_diagnosis: str | None = None
    differential_diagnoses: str | None = None
    icd_code: str | None = None


class PlanUpdate(BaseModel):
    treatment: str | None = None
    medications: str | None = None
    follow_up: str | None = None
    patient_education: str | None = None


class SoapNoteCreatedOut(BaseModel):
    id: int
    encounter_id: int
    note_type: str
    message: str = "Tạo SOAP note thành công"
