from src.agents.mcp.client import call_clinical_tool
from src.agents.state import ClinicalState


async def medical_normalize_node(state: ClinicalState) -> dict:
    try:
        normalized = await call_clinical_tool(
            "medical_normalize",
            {"text": state["transcript"]},
        )
        return {
            "normalized_transcript": normalized,
            "current_step": "medical_normalize",
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_step": "medical_normalize",
        }
