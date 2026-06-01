"""Provider abstraction for incident investigation LLM calls."""

from typing import Any, Protocol

from app.ai.llm_client import LLMClient
from app.core.config import settings


class LLMProvider(Protocol):
    provider_name: str

    async def analyze(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        ...


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    async def analyze(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        previous = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "openai"
        try:
            return await self.client.chat(system_prompt=system_prompt, user_message=user_message)
        finally:
            settings.LLM_PROVIDER = previous


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    async def analyze(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        previous = settings.LLM_PROVIDER
        settings.LLM_PROVIDER = "ollama"
        try:
            return await self.client.chat(system_prompt=system_prompt, user_message=user_message)
        finally:
            settings.LLM_PROVIDER = previous


class LLMProviderFactory:
    """Select the configured provider while allowing demo-safe fallback upstream."""

    @staticmethod
    def create() -> LLMProvider:
        if settings.LLM_PROVIDER == "ollama":
            return OllamaProvider()
        return OpenAIProvider()
