from pydantic import BaseModel, Field


class ClinicalSoapResponse(BaseModel):
    transcript: str = Field(..., description="Transcript thô từ ASR")
    normalized_transcript: str = Field(..., description="Transcript sau chuẩn hóa")
    facts: str = Field(..., description="Sự kiện y tế đã trích xuất (JSON)")
    soap_note: str = Field(..., description="SOAP note thô từ generate_soap")
    audited_soap: str = Field(..., description="SOAP note sau khi audit")


class ClinicalNoteOut(BaseModel):
    id: int
    transcript: str
    corrected_transcript: str
    soap_note: str
    audio_filename: str | None = None
    created_at: str

    model_config = {"from_attributes": True}
