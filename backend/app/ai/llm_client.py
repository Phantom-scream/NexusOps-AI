"""
NexusOps AI — LLM Client Abstraction Layer
Supports OpenAI API and Ollama (local) backends
"""
from collections.abc import AsyncIterator
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings

logger = structlog.get_logger(__name__)


class LLMClient:
    """
    Unified LLM client that abstracts over OpenAI and Ollama backends.
    Supports chat completion and embeddings.
    """

    def __init__(self):
        self._chat_model = None
        self._embeddings_model = None

    def _get_chat_model(self) -> ChatOpenAI:
        if self._chat_model is None:
            if settings.LLM_PROVIDER == "ollama":
                # Use LangChain's Ollama integration
                try:
                    from langchain_community.llms import Ollama
                    self._chat_model = Ollama(
                        base_url=settings.OLLAMA_BASE_URL,
                        model=settings.OLLAMA_MODEL,
                        temperature=0.1,
                    )
                except ImportError:
                    logger.warning("Ollama not available, falling back to OpenAI")
                    self._chat_model = self._build_openai_chat()
            else:
                self._chat_model = self._build_openai_chat()
        return self._chat_model

    def _build_openai_chat(self) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            timeout=60,
        )

    def _get_embeddings_model(self) -> OpenAIEmbeddings:
        if self._embeddings_model is None:
            self._embeddings_model = OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_EMBEDDING_MODEL,
            )
        return self._embeddings_model

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """
        Single chat turn with system + user messages.
        Returns: {"content": str, "tokens_used": int, "model": str}
        """
        model = self._get_chat_model()

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]

            response = await model.ainvoke(messages)

            tokens_used = None
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                tokens_used = response.usage_metadata.get("total_tokens")

            return {
                "content": response.content,
                "tokens_used": tokens_used,
                "model": settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else settings.OLLAMA_MODEL,
            }

        except Exception as exc:
            logger.error("LLM chat failed", error=str(exc), provider=settings.LLM_PROVIDER)
            raise

    async def chat_stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncIterator[str]:
        """Stream chat completions — yields token chunks."""
        model = self._get_chat_model()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        async for chunk in model.astream(messages):
            if chunk.content:
                yield chunk.content

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of text chunks."""
        embeddings_model = self._get_embeddings_model()
        try:
            return await embeddings_model.aembed_documents(texts)
        except Exception as exc:
            logger.error("Embedding generation failed", error=str(exc))
            raise

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query string."""
        embeddings_model = self._get_embeddings_model()
        try:
            return await embeddings_model.aembed_query(text)
        except Exception as exc:
            logger.error("Query embedding failed", error=str(exc))
            raise


# Module-level singleton
llm_client = LLMClient()
