from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from transformers import pipeline

from src.config import get_settings
from src.services.llm import get_llm
import torch

settings = get_settings()

if settings.openai_api_key:
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

ASR_MODEL = settings.asr_model_name



@lru_cache(maxsize=1)
def _get_transcriber():
    return pipeline(
        task="automatic-speech-recognition",
        model=ASR_MODEL,
    )


def transcribe_audio(audio_path: str) -> str:
    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file âm thanh: {audio_path}"
        )

    try:
        # ==========================================
        # PHẦN CODE CŨ (Đã comment lại để tránh Timeout)
        # ==========================================
        # import soundfile as sf
        # import numpy as np
        # audio_data, sampling_rate = sf.read(str(path))
        # 
        # if len(audio_data.shape) > 1:
        #     audio_data = audio_data.mean(axis=1)
        # 
        # # Resample to 16000Hz manually to avoid requiring torchaudio package for resampling
        # if sampling_rate != 16000:
        #     num_samples_target = int(len(audio_data) * 16000 / sampling_rate)
        #     old_indices = np.arange(len(audio_data))
        #     new_indices = np.linspace(0, len(audio_data) - 1, num_samples_target)
        #     audio_data = np.interp(new_indices, old_indices, audio_data).astype(np.float32)
        #     sampling_rate = 16000
        # 
        # result = _get_transcriber()(
        #     {"array": audio_data, "sampling_rate": sampling_rate},
        #     return_timestamps=True,
        #     chunk_length_s=30,
        #     generate_kwargs={
        #         "language": "vi",
        #         "task": "transcribe",
        #     },
        # )
        # 
        # text = result.get("text", "").strip()
        # ==========================================

        # ==========================================
        # PHẦN CODE MỚI (Dùng OpenAI API xử lý nhanh)
        # ==========================================
        from openai import OpenAI
        
        # Khởi tạo client, truyền trực tiếp API key từ settings
        client = OpenAI(api_key=settings.openai_api_key)
        
        with open(path, "rb") as audio_file:
            # Gọi API Whisper của OpenAI
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="vi" # Bắt buộc đầu ra tiếng Việt
            )
        
        text = transcript.text.strip()
        # ==========================================

        if not text:
            raise ValueError(
                "Không nhận diện được nội dung âm thanh"
            )

        return text

    except Exception as e:
        raise RuntimeError(
            f"Lỗi ASR: {str(e)}"
        ) from e


def fix_spelling(text: str) -> str:
    from langchain_core.messages import HumanMessage

    prompt = f"""
Bạn là chuyên gia hiệu đính transcript tiếng Việt từ hệ thống ASR.

Yêu cầu:
- Sửa lỗi chính tả.
- Sửa dấu câu.
- Viết hoa tên riêng nếu phù hợp.
- Giữ nguyên ý nghĩa gốc.
- Trong câu có thể xuất hiện thuật ngữ tiếng Anh.
- KHÔNG dịch thuật ngữ tiếng Anh sang tiếng Việt.
- Giữ nguyên tên sản phẩm, tên công nghệ, tên công ty, framework, API, model AI,...
- Nếu không chắc một từ là tiếng Việt hay tiếng Anh thì ưu tiên giữ nguyên.
- Không thêm nội dung mới.
- Không giải thích.
- Chỉ trả về văn bản đã hiệu đính.

Transcript:

{text}
"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    print("=== [fix_spelling] Response ===\n" + response.content.strip() + "\n")

    return response.content.strip()



def convert_to_soap_note(transcript: str) -> str:
    import json
    from langchain_core.messages import HumanMessage

    prompt = f"""
Bạn là Clinical Scribe AI hỗ trợ tạo SOAP Note từ transcript khám bệnh.

Mục tiêu:
* Chuyển transcript thành SOAP Note ngắn gọn, chính xác, phù hợp hồ sơ y khoa.
* Chỉ sử dụng thông tin xuất hiện trong transcript.
* Không suy diễn, không bổ sung dữ liệu ngoài transcript.
* Không tạo chẩn đoán mới nếu bác sĩ chưa đưa ra nhận định.
* Không thêm thuốc, xét nghiệm hoặc kế hoạch điều trị nếu bác sĩ không đề cập.

QUY TẮC PHÂN LOẠI:

[S] Subjective - Bao gồm:
- Lý do khám, triệu chứng bệnh nhân mô tả.
- Diễn tiến bệnh, tiền sử bệnh, thuốc đang dùng, dị ứng.
- KHÔNG bao gồm: kết quả khám, dấu hiệu sinh tồn, xét nghiệm, chẩn đoán.

[O] Objective - Bao gồm:
- Dấu hiệu sinh tồn, kết quả khám lâm sàng.
- Kết quả xét nghiệm, chẩn đoán hình ảnh.
- KHÔNG bao gồm: cảm nhận chủ quan, suy luận AI.

[A] Assessment - Bao gồm:
- Chẩn đoán hoặc nhận định được bác sĩ phát biểu rõ ràng.
- KHÔNG được tự tạo chẩn đoán.
- Nếu không có: ghi "Chưa ghi nhận đánh giá lâm sàng cụ thể."

[D] Diagnosis - Bao gồm:
- Chẩn đoán chính (primary_diagnosis).
- Chẩn đoán phân biệt (differential_diagnoses).
- Mã ICD nếu có (icd_code).

[P] Plan - Bao gồm:
- Xử trí / Điều trị (treatment).
- Thuốc kê (medications).
- Tái khám / Theo dõi (follow_up).
- Giáo dục bệnh nhân (patient_education).
- KHÔNG được tự đề xuất điều trị.

QUY TẮC XỬ LÝ THIẾU DỮ LIỆU:
Nếu mục không có trong transcript: ghi "Chưa ghi nhận".

TRẢ VỀ DẠNG JSON (chỉ JSON, KHÔNG thêm markdown hay giải thích):
{{
  "subjective": {{
    "chief_complaint": "...",
    "history": "...",
    "review_of_systems": "..."
  }},
  "objective": {{
    "vital_signs": "...",
    "physical_exam": "...",
    "lab_results": "..."
  }},
  "assessment": {{
    "diagnosis": "...",
    "severity": "...",
    "notes": "..."
  }},
  "diagnosis": {{
    "primary_diagnosis": "...",
    "differential_diagnoses": "...",
    "icd_code": "..."
  }},
  "plan": {{
    "treatment": "...",
    "medications": "...",
    "follow_up": "...",
    "patient_education": "..."
  }}
}}

Transcript:

{transcript}

"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    print("=== [convert_to_soap_note] Response ===\n" + raw + "\n")
    try:
        obj = json.loads(raw)
        return json.dumps(obj, ensure_ascii=False)
    except json.JSONDecodeError:
        import re
        cleaned = re.sub(r"```json\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        obj = json.loads(cleaned)
        return json.dumps(obj, ensure_ascii=False)


def medical_normalize(text: str) -> str:
    from langchain_core.messages import HumanMessage

    prompt = f"""
Bạn là chuyên gia hiệu đính và chuẩn hóa transcript y khoa tiếng Việt từ hệ thống ASR.

NHIỆM VỤ:
1. Sửa lỗi chính tả và dấu câu.
2. Chuẩn hóa thuật ngữ y khoa về đúng hình thức chuẩn.
3. Giữ nguyên ý nghĩa gốc.

QUY TẮC:
- Sửa lỗi chính tả tiếng Việt.
- Sửa dấu câu, viết hoa tên riêng nếu phù hợp.
- Chuẩn hóa thuật ngữ y khoa:
  + Viết đúng thuật ngữ y khoa chuẩn (VD: "đau đầu" thay vì "đau dau").
  + Giữ nguyên tên thuốc, tên bệnh nếu đã đúng.
  + Không dịch thuật ngữ tiếng Anh sang tiếng Việt.
- Giữ nguyên tên sản phẩm, tên công nghệ, tên công ty, framework, API, model AI.
- Nếu không chắc một từ là tiếng Việt hay tiếng Anh thì ưu tiên giữ nguyên.
- KHÔNG thêm nội dung mới.
- KHÔNG giải thích.
- Chỉ trả về văn bản đã chuẩn hóa.

Transcript:

{text}
"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    print("=== [medical_normalize] Response ===\n" + response.content.strip() + "\n")
    return response.content.strip()


def extract_facts(transcript: str) -> str:
    from langchain_core.messages import HumanMessage

    prompt = f"""
Bạn là trợ lý y khoa chuyên trích xuất thông tin y tế từ transcript.

NHIỆM VUY:
Phân tích transcript đã chuẩn hóa và trích xuất các sự kiện y tế quan trọng.

ĐỊNH DẠNG TRẢ VỀ (JSON):
{{
  "patient_info": {{
    "name": "Tên bệnh nhân nếu được nhắc đến",
    "age": "Tuổi nếu được nhắc đến",
    "gender": "Giới tính nếu được nhắc đến"
  }},
  "chief_complaint": "Lý do khám chính",
  "symptoms": ["Danh sách triệu chứng"],
  "vital_signs": {{
    "blood_pressure": "Huyết áp nếu có",
    "heart_rate": "Mạch nếu có",
    "temperature": "Nhiệt độ nếu có",
    "respiratory_rate": "Nhịp thở nếu có",
    "spo2": "SpO2 nếu có"
  }},
  "physical_exam": ["Kết quả khám lâm sàng"],
  "lab_results": ["Kết quả xét nghiệm nếu có"],
  "diagnosis": ["Chẩn đoán nếu bác sĩ đã kết luận"],
  "medications": ["Thuốc được kê"],
  "procedures": ["Thủ thuật, xét nghiệm được chỉ định"],
  "follow_up": "Hẹn tái khám nếu có",
  "additional_notes": ["Thông tin khác"]
}}

QUY TẮC:
- Chỉ trích xuất thông tin CÓ XUẤT HIỆN trong transcript.
- Nếu thông tin không có, để null hoặc array rỗng.
- KHÔNG tự suy diễn hoặc bổ sung thông tin ngoài transcript.
- Trả về JSON hợp lệ.

Transcript:

{transcript}
"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    print("=== [extract_facts] Response ===\n" + response.content.strip() + "\n")
    return response.content.strip()


def generate_soap(transcript: str, facts: str) -> str:
    import json
    from langchain_core.messages import HumanMessage

    prompt = f"""
Bạn là Clinical Scribe AI hỗ trợ tạo SOAP Note từ transcript và sự kiện y tế đã trích xuất.

NHIỆM VỤ:
Tạo SOAP Note chính xác, ngắn gọn, phù hợp hồ sơ y khoa.

ĐẦU VÀO:
1. Transcript đã chuẩn hóa.
2. Các sự kiện y tế đã trích xuất (JSON).

QUY TẮC PHÂN LOẠI:

[S] Subjective - Bao gồm:
- Lý do khám, triệu chứng bệnh nhân mô tả.
- Diễn tiến bệnh, tiền sử bệnh, thuốc đang dùng, dị ứng.
- KHÔNG bao gồm: kết quả khám, dấu hiệu sinh tồn, xét nghiệm, chẩn đoán.

[O] Objective - Bao gồm:
- Dấu hiệu sinh tồn, kết quả khám lâm sàng.
- Kết quả xét nghiệm, chẩn đoán hình ảnh.
- KHÔNG bao gồm: cảm nhận chủ quan, suy luận AI.

[A] Assessment - Bao gồm:
- Chẩn đoán hoặc nhận định được bác sĩ phát biểu rõ ràng.
- KHÔNG được tự tạo chẩn đoán.
- Nếu không có: ghi "Chưa ghi nhận đánh giá lâm sàng cụ thể."

[D] Diagnosis - Bao gồm:
- Chẩn đoán chính (primary_diagnosis).
- Chẩn đoán phân biệt (differential_diagnoses).
- Mã ICD nếu có (icd_code).

[P] Plan - Bao gồm:
- Xử trí / Điều trị (treatment).
- Thuốc kê (medications).
- Tái khám / Theo dõi (follow_up).
- Giáo dục bệnh nhân (patient_education).
- KHÔNG được tự đề xuất điều trị.

QUY TẮC XỬ LÝ THIẾU DỮ LIỆU:
Nếu mục không có trong transcript: ghi "Chưa ghi nhận".

TRẢ VỀ DẠNG JSON (chỉ JSON, KHÔNG thêm markdown hay giải thích):
{{
  "subjective": {{
    "chief_complaint": "...",
    "history": "...",
    "review_of_systems": "..."
  }},
  "objective": {{
    "vital_signs": "...",
    "physical_exam": "...",
    "lab_results": "..."
  }},
  "assessment": {{
    "diagnosis": "...",
    "severity": "...",
    "notes": "..."
  }},
  "diagnosis": {{
    "primary_diagnosis": "...",
    "differential_diagnoses": "...",
    "icd_code": "..."
  }},
  "plan": {{
    "treatment": "...",
    "medications": "...",
    "follow_up": "...",
    "patient_education": "..."
  }}
}}

Transcript:

{transcript}

Sự kiện y tế đã trích xuất:

{facts}
"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    print("=== [generate_soap] Response ===\n" + raw + "\n")
    try:
        obj = json.loads(raw)
        return json.dumps(obj, ensure_ascii=False)
    except json.JSONDecodeError:
        import re
        cleaned = re.sub(r"```json\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        obj = json.loads(cleaned)
        return json.dumps(obj, ensure_ascii=False)


def audit_soap(transcript: str, soap_note: str) -> str:
    import json
    from langchain_core.messages import HumanMessage

    prompt = f"""
Bạn là bác sĩ kiểm định viên kiểm tra chất lượng SOAP Note.

NHIỆM VỤ:
So sánh transcript gốc và SOAP Note (dạng JSON), phát hiện và sửa lỗi.

ĐẦU VÀO:
1. Transcript gốc.
2. SOAP Note dạng JSON với cấu trúc:
{{
  "subjective": {{"chief_complaint": "...", "history": "...", "review_of_systems": "..."}},
  "objective": {{"vital_signs": "...", "physical_exam": "...", "lab_results": "..."}},
  "assessment": {{"diagnosis": "...", "severity": "...", "notes": "..."}},
  "diagnosis": {{"primary_diagnosis": "...", "differential_diagnoses": "...", "icd_code": "..."}},
  "plan": {{"treatment": "...", "medications": "...", "follow_up": "...", "patient_education": "..."}}

}}

CÁC KIỂM TRA:

1. THÔNG TIN BỊ BỎ SÓT:
- So sánh các sự kiện trong transcript với nội dung SOAP.
- Nếu thông tin quan trọng có trong transcript nhưng thiếu trong SOAP → THÊM VÀO.

2. THÔNG TIN KHÔNG TỒN TẠI:
- Nếu nội dung trong SOAP KHÔNG có trong transcript → XÓA.

3. PHÂN LOẠI SAI:
- Kiểm tra từng mục S/O/A/D/P có đúng vị trí không.
- Nếu thông tin phân loại sai → CHUYỂN VỀ ĐÚNG MỤC.

4. LỖI KHÁC:
- Sai thuật ngữ y khoa.
- Mâu thuẫn nội bộ.

QUY TẮC XỬ LÝ:
- Nếu phát hiện lỗi: sửa SOAP và trả về SOAP đã sửa.
- Nếu không có lỗi: giữ nguyên SOAP gốc.
- Nếu một mục không có trong transcript: giữ nguyên giá trị "Chưa ghi nhận".

TRẢ VỀ DẠNG JSON (chỉ JSON, KHÔNG thêm markdown hay giải thích):
{{
  "review": "Nhận xét so sánh giữa SOAP và Transcript: liệt kê những gì đã khớp, những gì bị thiếu, bị thừa, hoặc phân loại sai. Viết ngắn gọn bằng tiếng Việt.",
  "subjective": {{"chief_complaint": "...", "history": "...", "review_of_systems": "..."}},
  "objective": {{"vital_signs": "...", "physical_exam": "...", "lab_results": "..."}},
  "assessment": {{"diagnosis": "...", "severity": "...", "notes": "..."}},
  "diagnosis": {{"primary_diagnosis": "...", "differential_diagnoses": "...", "icd_code": "..."}},
  "plan": {{"treatment": "...", "medications": "...", "follow_up": "...", "patient_education": "..."}}
}}

Transcript gốc:

{transcript}

SOAP Note cần kiểm tra:

{soap_note}
"""

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    print("=== [audit_soap] Response ===\n" + raw + "\n")
    try:
        obj = json.loads(raw)
        return json.dumps(obj, ensure_ascii=False)
    except json.JSONDecodeError:
        import re
        cleaned = re.sub(r"```json\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()
        obj = json.loads(cleaned)
        return json.dumps(obj, ensure_ascii=False)



def find_patient_visit_info(
    full_name: str | None = None,
    date_of_birth: str | None = None,
    phone: str | None = None,
) -> str:
    from src.database.engine import SessionLocal
    from src.api.patients.repository import find_patient_by_info

    db = SessionLocal()
    try:
        result = find_patient_by_info(db, full_name=full_name, date_of_birth=date_of_birth, phone=phone)
        if not result:
            return json.dumps({"found": False, "message": "Không tìm thấy bệnh nhân"}, ensure_ascii=False)

        patient = result["patient"]
        last_encounter = result["last_encounter"]

        soap_data = None
        if last_encounter and last_encounter.get("soap_note"):
            soap_data = last_encounter["soap_note"]

        return json.dumps(
            {
                "found": True,
                "patient": {
                    "id": patient.id,
                    "full_name": patient.full_name,
                    "date_of_birth": patient.date_of_birth,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "address": patient.address,
                    "medical_record_no": patient.medical_record_no,
                },
                "has_been_visited": result["has_been_visited"],
                "encounter_count": result["encounter_count"],
                "last_encounter": {
                    "id": last_encounter["id"],
                    "encounter_date": last_encounter["encounter_date"],
                    "status": last_encounter["status"],
                    "doctor_name": last_encounter["doctor_name"],
                    "soap_note": soap_data,
                }
                if last_encounter
                else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    finally:
        db.close()
