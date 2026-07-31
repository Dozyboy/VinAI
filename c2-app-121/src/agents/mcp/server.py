import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from fastmcp import FastMCP

from src.agents.tools.clinical import (
    audit_soap as _audit_soap,
    convert_to_soap_note as _convert_to_soap_note,
    extract_facts as _extract_facts,
    find_patient_visit_info as _find_patient_visit_info,
    fix_spelling as _fix_spelling,
    generate_soap as _generate_soap,
    medical_normalize as _medical_normalize,
    transcribe_audio as _transcribe_audio,
)

mcp = FastMCP("clinical-tools")


@mcp.tool()
def transcribe_audio(audio_path: str) -> str:
    """Chuyển file âm thanh khám bệnh thành transcript tiếng Việt."""
    return _transcribe_audio(audio_path)


@mcp.tool()
def fix_spelling(text: str) -> str:
    """Hiệu đính chính tả và dấu câu cho transcript ASR."""
    return _fix_spelling(text)


@mcp.tool()
def convert_to_soap_note(transcript: str) -> str:
    """Chuyển transcript khám bệnh thành SOAP note."""
    return _convert_to_soap_note(transcript)


@mcp.tool()
def medical_normalize(text: str) -> str:
    """Chuẩn hóa transcript y khoa: sửa lỗi chính tả, chuẩn hóa thuật ngữ y tế."""
    return _medical_normalize(text)


@mcp.tool()
def extract_facts(transcript: str) -> str:
    """Trích xuất sự kiện y tế từ transcript đã chuẩn hóa (trả về JSON)."""
    return _extract_facts(transcript)


@mcp.tool()
def generate_soap(transcript: str, facts: str) -> str:
    """Tạo SOAP Note từ transcript và sự kiện y tế đã trích xuất."""
    return _generate_soap(transcript, facts)


@mcp.tool()
def audit_soap(transcript: str, soap_note: str) -> str:
    """Kiểm tra và sửa SOAP Note bằng cách so sánh với transcript gốc."""
    return _audit_soap(transcript, soap_note)


@mcp.tool()
def find_patient_visit_info(
    full_name: str | None = None,
    date_of_birth: str | None = None,
    phone: str | None = None,
) -> str:
    """Tìm kiếm bệnh nhân theo tên, ngày sinh, SĐT và kiểm tra lịch sử khám bệnh cùng SOAP note gần nhất."""
    return _find_patient_visit_info(full_name=full_name, date_of_birth=date_of_birth, phone=phone)


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8001"))
    mcp.run(transport="http", host="0.0.0.0", port=port)
