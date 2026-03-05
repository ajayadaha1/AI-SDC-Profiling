"""AMD LLM Gateway wrapper using AsyncOpenAI with Ocp-Apim-Subscription-Key auth."""

import os
import json
import logging
from typing import Any

import openai

from app.config import get_settings

logger = logging.getLogger(__name__)


class AIClient:
    """Wrapper for AMD LLM Gateway API calls."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = openai.AsyncOpenAI(
            base_url=settings.LLM_ENDPOINT,
            api_key="dummy",  # Actual auth via header
            timeout=settings.LLM_TIMEOUT,
            default_headers={
                "Ocp-Apim-Subscription-Key": settings.LLM_API_KEY,
                "user": os.getenv("USER", os.getenv("USERNAME", "ai-sdc-profiling")),
            },
        )
        self.model = settings.LLM_MODEL

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, str] | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request and return the response content."""
        params: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            params["response_format"] = response_format

        for attempt in range(3):
            try:
                response = await self.client.chat.completions.create(**params)
                content = response.choices[0].message.content
                logger.debug("LLM response (attempt %d): %s", attempt + 1, content[:200])
                return content
            except Exception:
                if attempt == 2:
                    raise
                logger.warning("LLM call failed (attempt %d/3), retrying...", attempt + 1)

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a chat request and parse the response as JSON."""
        raw = await self.chat(
            messages,
            temperature=temperature,
            response_format={"type": "json_object"},
            max_tokens=max_tokens,
        )
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # drop opening ```json
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return json.loads(text)

    async def test_connection(self) -> dict:
        """Ping the LLM Gateway to verify connectivity."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return {"status": "connected", "model": self.model}
        except Exception as e:
            return {"status": "failed", "model": self.model, "error": str(e)}


_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
