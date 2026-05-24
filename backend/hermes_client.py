"""Hermes Agent API client — wraps the OpenAI-compatible endpoint with session ID support."""
import json
from typing import AsyncIterator
import httpx
from openai import AsyncOpenAI

class HermesClient:
    def __init__(self, base_url: str, api_key: str = "hermes", model: str = "hermes"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._openai = AsyncOpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=api_key,
        )

    async def chat(
        self,
        messages: list[dict],
        session_id: str,
        temperature: float = 0.3,
    ) -> str:
        """Non-streaming chat — returns full response string."""
        response = await self._openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            extra_headers={"X-Hermes-Session-Id": session_id},
        )
        return response.choices[0].message.content or ""

    async def stream_chat(
        self,
        messages: list[dict],
        session_id: str,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Streaming chat — yields text chunks as they arrive."""
        stream = await self._openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True,
            extra_headers={"X-Hermes-Session-Id": session_id},
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def create_job(self, name: str, schedule: str, prompt: str) -> dict:
        """Register a cron job with Hermes scheduler."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/jobs",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"name": name, "schedule": schedule, "prompt": prompt},
                timeout=10.0,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            return {"error": resp.text, "status": resp.status_code}

    async def list_jobs(self) -> list[dict]:
        """List all registered Hermes cron jobs."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/jobs",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            if resp.status_code == 200:
                return resp.json()
            return []
