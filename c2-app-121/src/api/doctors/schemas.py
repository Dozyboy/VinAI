from pydantic import BaseModel, Field


class DoctorOut(BaseModel):
    id: int
    full_name: str
    specialization: str
    email: str | None = None
    phone: str | None = None
    is_active: bool = True
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DoctorCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    specialization: str = Field(default="", max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    specialization: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class DoctorDetail(DoctorOut):
    shift_count: int = 0
    encounter_count: int = 0
    patient_count: int = 0


class DoctorStats(BaseModel):
    total_encounters: int = 0
    completed_encounters: int = 0
    in_progress_encounters: int = 0
    total_patients: int = 0
    total_shifts: int = 0


class DoctorList(BaseModel):
    items: list[DoctorOut]
    total: int
    page: int
    size: int
    pages: int
