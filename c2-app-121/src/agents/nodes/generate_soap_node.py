from src.agents.mcp.client import call_clinical_tool
from src.agents.state import ClinicalState


async def generate_soap_node(state: ClinicalState) -> dict:
    try:
        soap_note = await call_clinical_tool(
            "generate_soap",
            {
                "transcript": state["normalized_transcript"],
                "facts": state["facts"],
            },
        )
        return {
            "soap_note": soap_note,
            "current_step": "generate_soap",
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_step": "generate_soap",
        }
