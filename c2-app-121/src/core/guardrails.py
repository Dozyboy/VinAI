from __future__ import annotations

import re


class GuardrailViolationError(ValueError):
    """Raised when an input or model output fails a production guardrail."""


REQUIRED_SOAP_SECTIONS = {
    "S": re.compile(r"(^|\n)\s*#?\s*S\s*[-:]", re.IGNORECASE),
    "O": re.compile(r"(^|\n)\s*#?\s*O\s*[-:]", re.IGNORECASE),
    "A": re.compile(r"(^|\n)\s*#?\s*A\s*[-:]", re.IGNORECASE),
    "P": re.compile(r"(^|\n)\s*#?\s*P\s*[-:]", re.IGNORECASE),
}


def validate_audio_size(file_bytes: bytes, max_mb: int) -> None:
    max_bytes = max_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise GuardrailViolationError(
            f"Audio file is too large. Maximum allowed size is {max_mb} MB."
        )


def validate_transcript_text(text: str, max_chars: int) -> str:
    clean_text = (text or "").strip()
    if not clean_text:
        raise GuardrailViolationError("Transcript is empty.")
    if len(clean_text) > max_chars:
        raise GuardrailViolationError(
            f"Transcript is too long. Maximum allowed length is {max_chars} characters."
        )
    return clean_text


def wrap_untrusted_transcript(text: str) -> str:
    return f"<transcript>\n{text}\n</transcript>"


def missing_soap_sections(note: str) -> list[str]:
    return [
        section
        for section, pattern in REQUIRED_SOAP_SECTIONS.items()
        if not pattern.search(note or "")
    ]


def validate_soap_note(note: str) -> str:
    clean_note = (note or "").strip()
    if not clean_note:
        raise GuardrailViolationError("SOAP note is empty.")

    missing = missing_soap_sections(clean_note)
    if missing:
        raise GuardrailViolationError(
            "SOAP note is missing required sections: " + ", ".join(missing)
        )

    return clean_note
