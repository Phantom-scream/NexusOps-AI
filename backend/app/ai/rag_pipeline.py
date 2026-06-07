"""
NexusOps AI — RAG (Retrieval-Augmented Generation) Pipeline
Vector search over indexed infrastructure knowledge
"""
from typing import Any

import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.ai.llm_client import llm_client
from app.ai.prompts.templates import RAG_QUERY_SYSTEM_PROMPT, RAG_QUERY_USER_TEMPLATE
from app.core.config import settings

logger = structlog.get_logger(__name__)

EMBEDDING_DIM = 1536  # text-embedding-ada-002 dimension


class RAGPipeline:
    """
    RAG pipeline using Qdrant for vector storage and similarity search.

    Indexes:
    - Past incident reports
    - Kubernetes manifests
    - Terraform configurations
    - Runbooks and documentation
    """

    def __init__(self):
        self._client: AsyncQdrantClient | None = None

    async def _get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=10,
            )
            await self._ensure_collections()
        return self._client

    async def _ensure_collections(self) -> None:
        """Create Qdrant collections if they don't exist."""
        client = self._client

        collections_response = await client.get_collections()
        existing = {c.name for c in collections_response.collections}

        for collection_name in [
            settings.QDRANT_COLLECTION_INCIDENTS,
            settings.QDRANT_COLLECTION_INFRA,
        ]:
            if collection_name not in existing:
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection", collection=collection_name)

    async def index_incident(
        self,
        incident_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index an incident report into the vector store."""
        try:
            client = await self._get_client()
            vector = await llm_client.embed_query(content)

            point = PointStruct(
                id=self._hash_id(incident_id),
                vector=vector,
                payload={
                    "incident_id": incident_id,
                    "content": content[:2000],
                    "doc_type": "incident",
                    **(metadata or {}),
                },
            )

            await client.upsert(
                collection_name=settings.QDRANT_COLLECTION_INCIDENTS,
                points=[point],
            )
            logger.info("Indexed incident", incident_id=incident_id)

        except Exception as exc:
            logger.error("Failed to index incident", incident_id=incident_id, error=str(exc))

    async def index_infrastructure_doc(
        self,
        doc_id: str,
        content: str,
        doc_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Index infrastructure documents (manifests, Terraform, runbooks)."""
        try:
            client = await self._get_client()

            # Chunk large documents
            chunks = self._chunk_text(content, chunk_size=1000)

            points = []
            for i, chunk in enumerate(chunks):
                vector = await llm_client.embed_query(chunk)
                points.append(
                    PointStruct(
                        id=self._hash_id(f"{doc_id}-{i}"),
                        vector=vector,
                        payload={
                            "doc_id": doc_id,
                            "chunk_index": i,
                            "content": chunk,
                            "doc_type": doc_type,
                            **(metadata or {}),
                        },
                    )
                )

            await client.upsert(
                collection_name=settings.QDRANT_COLLECTION_INFRA,
                points=points,
            )
            logger.info("Indexed infrastructure doc", doc_id=doc_id, doc_type=doc_type, chunks=len(chunks))

        except Exception as exc:
            logger.error("Failed to index infrastructure doc", doc_id=doc_id, error=str(exc))

    async def search_incidents(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.70,
    ) -> list[dict[str, Any]]:
        """Search past incidents by semantic similarity."""
        try:
            client = await self._get_client()
            query_vector = await llm_client.embed_query(query)

            results = await client.search(
                collection_name=settings.QDRANT_COLLECTION_INCIDENTS,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )

            return [
                {
                    "score": r.score,
                    "content": r.payload.get("content", ""),
                    "incident_id": r.payload.get("incident_id"),
                    "metadata": {k: v for k, v in r.payload.items() if k not in ("content",)},
                }
                for r in results
            ]

        except Exception as exc:
            logger.warning("Incident vector search failed", error=str(exc))
            return []

    async def search_infrastructure(
        self,
        query: str,
        doc_type: str | None = None,
        limit: int = 5,
        score_threshold: float = 0.65,
    ) -> list[dict[str, Any]]:
        """Search infrastructure documents by semantic similarity."""
        try:
            client = await self._get_client()
            query_vector = await llm_client.embed_query(query)

            search_filter = None
            if doc_type:
                search_filter = Filter(
                    must=[FieldCondition(key="doc_type", match=MatchValue(value=doc_type))]
                )

            results = await client.search(
                collection_name=settings.QDRANT_COLLECTION_INFRA,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
            )

            return [
                {
                    "score": r.score,
                    "content": r.payload.get("content", ""),
                    "doc_type": r.payload.get("doc_type"),
                    "doc_id": r.payload.get("doc_id"),
                }
                for r in results
            ]

        except Exception as exc:
            logger.warning("Infrastructure vector search failed", error=str(exc))
            return []

    async def rag_query(self, query: str) -> dict[str, Any]:
        """
        Full RAG Q&A: retrieve relevant docs, then generate an LLM answer.
        """
        # Search both collections
        incident_results = await self.search_incidents(query, limit=3)
        infra_results = await self.search_infrastructure(query, limit=3)

        all_results = incident_results + infra_results
        all_results.sort(key=lambda x: x["score"], reverse=True)

        if not all_results:
            context = "No relevant infrastructure knowledge found in the index."
        else:
            context_parts = []
            for r in all_results[:5]:
                prefix = f"[{r.get('doc_type', 'incident').upper()}] "
                context_parts.append(prefix + r["content"])
            context = "\n\n---\n\n".join(context_parts)

        user_message = RAG_QUERY_USER_TEMPLATE.format(
            query=query,
            context=context,
        )

        response = await llm_client.chat(
            system_prompt=RAG_QUERY_SYSTEM_PROMPT,
            user_message=user_message,
        )

        return {
            "answer": response["content"],
            "sources": all_results[:5],
            "tokens_used": response.get("tokens_used"),
        }

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        overlap = 100

        i = 0
        while i < len(words):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap

        return chunks if chunks else [text]

    def _hash_id(self, text: str) -> int:
        """Convert a string ID to a stable integer for Qdrant."""
        import hashlib
        return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
