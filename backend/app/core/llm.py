import json
from collections.abc import AsyncGenerator

import httpx

from app.config import settings


class LLMService:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.ollama_model

    async def generate(self, prompt: str) -> str:
        """Non-streaming generation. Returns the full response string."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Streaming generation via Ollama's line-delimited JSON protocol.
        Each line: {"model": "...", "response": "token", "done": false}
        Yields individual token strings.
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break

    def list_available_models(self) -> list[str]:
        """Synchronous model list — used only at startup/health check."""
        import httpx as _httpx
        try:
            resp = _httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []
