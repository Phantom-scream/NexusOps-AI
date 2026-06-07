# ADR-005: Vector Database Selection

## Context

AI investigation requires retrieval of relevant incidents, logs, events, traces, investigation history, and operational knowledge. The platform needs a vector store that can run locally, support semantic search, and fit into Docker Compose demonstrations.

## Decision

Use Qdrant as the vector database for RAG workflows.

Qdrant is lightweight for local deployment, has a clear API, supports metadata filtering, and is credible for production-like vector retrieval scenarios.

## Alternatives

- **PostgreSQL with pgvector:** attractive for reducing infrastructure components, but the project benefits from demonstrating a dedicated vector database.
- **Pinecone/managed vector DB:** production-ready, but requires external accounts and weakens offline demo capability.
- **In-memory search:** simple, but not representative of real RAG architecture.

## Consequences

- RAG flows can index investigation history and telemetry evidence independently from relational storage.
- Local demos remain self-contained.
- The platform must define retention and reindexing strategies before scaling vector data heavily.
