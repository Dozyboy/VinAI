from langgraph.graph import END, StateGraph

from src.agents.nodes.audit_soap_node import audit_soap_node
from src.agents.nodes.extract_facts_node import extract_facts_node
from src.agents.nodes.generate_soap_node import generate_soap_node
from src.agents.nodes.medical_normalize_node import medical_normalize_node
from src.agents.nodes.transcribe_node import transcribe_node
from src.agents.state import ClinicalState


def route_after_transcribe(state: ClinicalState) -> str:
    if state.get("error"):
        return END
    return "medical_normalize"


def route_after_medical_normalize(state: ClinicalState) -> str:
    if state.get("error"):
        return END
    return "extract_facts"


def route_after_extract_facts(state: ClinicalState) -> str:
    if state.get("error"):
        return END
    return "generate_soap"


def route_after_generate_soap(state: ClinicalState) -> str:
    if state.get("error"):
        return END
    return "audit_soap"


def build_graph() -> StateGraph:
    graph = StateGraph(ClinicalState)

    graph.add_node("transcribe", transcribe_node)
    graph.add_node("medical_normalize", medical_normalize_node)
    graph.add_node("extract_facts", extract_facts_node)
    graph.add_node("generate_soap", generate_soap_node)
    graph.add_node("audit_soap", audit_soap_node)

    graph.set_entry_point("transcribe")
    graph.add_conditional_edges("transcribe", route_after_transcribe)
    graph.add_conditional_edges("medical_normalize", route_after_medical_normalize)
    graph.add_conditional_edges("extract_facts", route_after_extract_facts)
    graph.add_conditional_edges("generate_soap", route_after_generate_soap)
    graph.add_edge("audit_soap", END)

    return graph.compile()


clinical_agent = build_graph()
