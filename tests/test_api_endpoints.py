import pytest
import httpx
from backend.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_system_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/system")
    assert response.status_code == 200
    data = response.json()
    assert "vector_dimension" in data
    assert data["vector_dimension"] == 768

@pytest.mark.asyncio
async def test_documents_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/documents?collection=enterprise")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_ask_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/ask", json={"query": "What is photosynthesis?", "collection": "enterprise"})
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert len(data["sources"]) > 0

@pytest.mark.asyncio
async def test_stt_status_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/stt/status")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "sarvam"
    assert len(data["supported_languages"]) > 0
