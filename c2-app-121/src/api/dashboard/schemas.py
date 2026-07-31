from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_doctors: int = 0
    total_patients: int = 0
    total_encounters: int = 0
    completed_encounters: int = 0
    in_progress_encounters: int = 0
    today_encounters: int = 0
    total_recordings: int = 0


class DoctorWorkloadItem(BaseModel):
    doctor_id: int
    doctor_name: str
    specialization: str
    encounter_count: int
    patient_count: int


class DoctorWorkload(BaseModel):
    items: list[DoctorWorkloadItem]


class TopDiagnosisItem(BaseModel):
    diagnosis: str
    count: int


class TopDiagnoses(BaseModel):
    items: list[TopDiagnosisItem]


class MonthlyTrendItem(BaseModel):
    month: str
    count: int


class MonthlyTrend(BaseModel):
    items: list[MonthlyTrendItem]


# ── Daily View ──


class EncounterBrief(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    chief_complaint: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class ShiftDaily(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str
    specialization: str
    start_time: str
    end_time: str
    status: str
    encounters: list[EncounterBrief] = []
    encounter_count: int = 0


class DailyViewResponse(BaseModel):
    date: str
    shifts: list[ShiftDaily] = []
    unassigned_encounters: list[EncounterBrief] = []
