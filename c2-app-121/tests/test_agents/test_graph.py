from langgraph.graph import END

from src.agents.graph import (
    clinical_agent,
    route_after_transcribe,
    route_after_medical_normalize,
    route_after_extract_facts,
    route_after_generate_soap,
)


def test_clinical_agent_compiles():
    assert clinical_agent is not None


def test_route_after_transcribe_stops_on_error():
    assert route_after_transcribe({"error": "ASR failed"}) == END


def test_route_after_transcribe_continues_without_error():
    assert route_after_transcribe({"transcript": "Benh nhan dau dau"}) == "medical_normalize"


def test_route_after_medical_normalize_stops_on_error():
    assert route_after_medical_normalize({"error": "Failed"}) == END


def test_route_after_medical_normalize_continues_without_error():
    assert route_after_medical_normalize({"normalized_transcript": "..."}) == "extract_facts"


def test_route_after_extract_facts_stops_on_error():
    assert route_after_extract_facts({"error": "Failed"}) == END


def test_route_after_extract_facts_continues_without_error():
    assert route_after_extract_facts({"clinical_facts": "..."}) == "generate_soap"


def test_route_after_generate_soap_stops_on_error():
    assert route_after_generate_soap({"error": "Failed"}) == END


def test_route_after_generate_soap_continues_without_error():
    assert route_after_generate_soap({"soap_note": "..."}) == "audit_soap"
