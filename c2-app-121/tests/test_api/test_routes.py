import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_api_status(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["pipeline"] == ["transcribe", "fix_spelling", "soap"]


@pytest.mark.asyncio
async def test_clinical_endpoint_requires_auth(client):
    response = await client.post(
        "/api/v1/clinical/soap-note",
        files={"file": ("note.txt", b"not audio", "text/plain")},
    )
    assert response.status_code in {401, 403}
