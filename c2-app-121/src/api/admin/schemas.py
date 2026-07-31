from pydantic import BaseModel


class AdminStats(BaseModel):
    total_users: int
    total_notes: int
    active_users: int
    total_doctors: int = 0
    total_patients: int = 0
    total_encounters: int = 0
    total_shifts: int = 0
    completed_encounters: int = 0


class AdminUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}
