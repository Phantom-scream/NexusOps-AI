# ADR-002: PostgreSQL Selection

## Context

The platform stores interconnected infrastructure, telemetry, incident, security, cost, AI investigation, and audit data. These entities require durable persistence, relational queries, transactions, indexing, migrations, and a schema that can be explained clearly during architecture review.

## Decision

Use PostgreSQL as the primary system of record.

PostgreSQL provides relational integrity, JSON support for provider metadata, mature indexing, transactional guarantees, and strong operational familiarity for cloud platform teams.

## Alternatives

- **MongoDB:** flexible document model, but weaker fit for topology relationships, joins, and audit consistency.
- **SQLite:** excellent local simplicity, but not representative of production platform architecture.
- **DynamoDB/Cassandra:** useful at very high scale, but premature for this project and less convenient for relational topology.

## Consequences

- Relationships between clusters, workloads, telemetry, incidents, scans, and reports remain queryable.
- Alembic migrations provide schema evolution.
- Future scaling can use indexes, partitioning, read replicas, and retention strategies before changing databases.
- The implementation must avoid high-cardinality telemetry patterns that overload relational storage.
