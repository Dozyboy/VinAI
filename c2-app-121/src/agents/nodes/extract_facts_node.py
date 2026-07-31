from src.agents.mcp.client import call_clinical_tool
from src.agents.state import ClinicalState


async def extract_facts_node(state: ClinicalState) -> dict:
    try:
        facts = await call_clinical_tool(
            "extract_facts",
            {"transcript": state["normalized_transcript"]},
        )
        return {
            "facts": facts,
            "current_step": "extract_facts",
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_step": "extract_facts",
        }
