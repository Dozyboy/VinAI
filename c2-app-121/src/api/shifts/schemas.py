from pydantic import BaseModel, Field


class ShiftOut(BaseModel):
    id: int
    doctor_id: int
    shift_date: str
    start_time: str
    end_time: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class ShiftWithDoctor(ShiftOut):
    doctor_name: str = ""
    doctor_specialization: str = ""


class ShiftCreate(BaseModel):
    doctor_id: int = Field(..., ge=1)
    shift_date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM")
    end_time: str = Field(..., description="HH:MM")
    status: str = Field(default="scheduled", pattern=r"^(scheduled|in_progress|completed|cancelled)$")


class ShiftUpdate(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(scheduled|in_progress|completed|cancelled)$")
    start_time: str | None = None
    end_time: str | None = None


class ShiftList(BaseModel):
    items: list[ShiftWithDoctor]
    total: int
    page: int
    size: int
    pages: int
