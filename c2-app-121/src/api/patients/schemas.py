from pydantic import BaseModel, Field


class PatientOut(BaseModel):
    id: int
    full_name: str
    date_of_birth: str | None = None
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    medical_record_no: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    date_of_birth: str | None = None
    gender: str | None = Field(default=None, pattern=r"^(male|female|other)$")
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    medical_record_no: str | None = Field(default=None, max_length=100)


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: str | None = None
    gender: str | None = Field(default=None, pattern=r"^(male|female|other)$")
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    medical_record_no: str | None = Field(default=None, max_length=100)


class PatientDetail(PatientOut):
    encounter_count: int = 0


class PatientList(BaseModel):
    items: list[PatientOut]
    total: int
    page: int
    size: int
    pages: int


class SoapSubjectiveInfo(BaseModel):
    chief_complaint: str = ""
    history: str = ""
    review_of_systems: str = ""


class SoapObjectiveInfo(BaseModel):
    vital_signs: str = ""
    physical_exam: str = ""
    lab_results: str = ""


class SoapPlanInfo(BaseModel):
    treatment: str = ""
    medications: str = ""
    follow_up: str = ""
    patient_education: str = ""


class SoapDiagnosisDetailInfo(BaseModel):
    primary_diagnosis: str = ""
    differential_diagnoses: str = ""
    icd_code: str | None = None
    plan: SoapPlanInfo | None = None


class SoapAssessmentInfo(BaseModel):
    diagnosis: str = ""
    severity: str = ""
    notes: str = ""
    diagnosis_detail: SoapDiagnosisDetailInfo | None = None


class SoapNoteInfo(BaseModel):
    id: int
    note_type: str
    subjective: SoapSubjectiveInfo | None = None
    objective: SoapObjectiveInfo | None = None
    assessment: SoapAssessmentInfo | None = None


class LastEncounterInfo(BaseModel):
    id: int
    encounter_date: str
    status: str
    chief_complaint: str
    doctor_name: str | None = None
    soap_note: SoapNoteInfo | None = None


class PatientEncounterCheck(BaseModel):
    patient: PatientOut
    has_been_visited: bool
    encounter_count: int
    last_encounter: LastEncounterInfo | None = None
