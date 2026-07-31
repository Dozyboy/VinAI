from src.agents.mcp.client import call_clinical_tool
from src.agents.state import ClinicalState


async def audit_soap_node(state: ClinicalState) -> dict:
    try:
        audited_soap = await call_clinical_tool(
            "audit_soap",
            {
                "transcript": state["transcript"],
                "soap_note": state["soap_note"],
            },
        )
        return {
            "audited_soap": audited_soap,
            "current_step": "audit_soap",
        }
    except Exception as e:
        return {
            "error": str(e),
            "current_step": "audit_soap",
        }
