from unittest.mock import AsyncMock, patch


def test_query_non_streaming(client, mock_embedding, mock_vectorstore):
    with patch("app.services.query_service.LLMService") as MockLLM:
        instance = MockLLM.return_value
        instance.model = "llama3.2:3b"
        instance.generate = AsyncMock(return_value="The attention mechanism is the main contribution.")

        resp = client.post(
            "/api/v1/query/",
            json={"query": "What is the main contribution?", "top_k": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert "model_used" in data
        assert len(data["citations"]) > 0
        assert data["citations"][0]["filename"] == "test.pdf"


def test_query_missing_body(client):
    resp = client.post("/api/v1/query/", json={})
    assert resp.status_code == 422


def test_query_empty_string(client):
    resp = client.post("/api/v1/query/", json={"query": ""})
    assert resp.status_code == 422


def test_health_endpoint(client):
    with patch("app.api.v1.health.httpx.AsyncClient") as _:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "services" in data
