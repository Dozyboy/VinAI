from __future__ import annotations

from typing import TypedDict, Optional


class ClinicalState(TypedDict, total=False):
    audio_path: str
    transcript: Optional[str]
    normalized_transcript: Optional[str]
    facts: Optional[str]
    soap_note: Optional[str]
    audited_soap: Optional[str]
    current_step: Optional[str]
    error: Optional[str]
