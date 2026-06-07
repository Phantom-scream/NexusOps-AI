"""
NexusOps AI — Application Configuration
Centralized settings management using Pydantic Settings
"""
import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_csv_or_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else [value]
    except (json.JSONDecodeError, ValueError):
        return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ----------------------------------------------------------
    # Application
    # ----------------------------------------------------------
    APP_NAME: str = "NexusOps AI"
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_VERSION: str = "0.1.0"
    SECRET_KEY: str = "change-me-in-production"
    API_PREFIX: str = "/api/v1"

    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://nexusops:nexusops_secret@localhost:5432/nexusops"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ----------------------------------------------------------
    # Redis
    # ----------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ----------------------------------------------------------
    # Qdrant
    # ----------------------------------------------------------
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_INFRA: str = "infrastructure_vectors"
    QDRANT_COLLECTION_INCIDENTS: str = "incident_vectors"

    # ----------------------------------------------------------
    # AI / LLM
    # ----------------------------------------------------------
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_MAX_TOKENS: int = 4096

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"

    LLM_PROVIDER: str = "openai"  # openai | ollama

    # ----------------------------------------------------------
    # Kafka / Redpanda
    # ----------------------------------------------------------
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_EVENTS: str = "nexusops.events"
    KAFKA_TOPIC_INCIDENTS: str = "nexusops.incidents"
    KAFKA_TOPIC_METRICS: str = "nexusops.metrics"
    KAFKA_CONSUMER_GROUP: str = "nexusops-consumer"

    # ----------------------------------------------------------
    # Kubernetes
    # ----------------------------------------------------------
    KUBECONFIG_PATH: str = "~/.kube/config"
    K8S_IN_CLUSTER: bool = False
    K8S_API_TIMEOUT: int = 30

    # ----------------------------------------------------------
    # Security / Auth
    # ----------------------------------------------------------
    JWT_SECRET_KEY: str = "change-me-in-production-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "nexusops-ai"
    JWT_AUDIENCE: str = "nexusops-api"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Comma-separated string to avoid pydantic-settings v2 JSON-decode issues with List[str]
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    CORS_HEADERS: str = "Authorization,Content-Type,X-Request-ID"

    @property
    def cors_origins_list(self) -> list[str]:
        return _parse_csv_or_json_list(self.CORS_ORIGINS)

    @property
    def cors_methods_list(self) -> list[str]:
        return _parse_csv_or_json_list(self.CORS_METHODS)

    @property
    def cors_headers_list(self) -> list[str]:
        return _parse_csv_or_json_list(self.CORS_HEADERS)

    RATE_LIMIT_PER_MINUTE: int = 60
    SECURITY_HEADERS_ENABLED: bool = True

    # ----------------------------------------------------------
    # Observability
    # ----------------------------------------------------------
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "nexusops-backend"
    PROMETHEUS_METRICS_PORT: int = 9090

    # ----------------------------------------------------------
    # Security Scanning
    # ----------------------------------------------------------
    TRIVY_SERVER_URL: str = "http://localhost:4954"
    OPA_SERVER_URL: str = "http://localhost:8181"

    # ----------------------------------------------------------
    # Logging
    # ----------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    def validate_production_safety(self) -> None:
        """Block common unsafe production configuration mistakes at startup."""
        if not self.is_production:
            return

        unsafe_values = {
            "SECRET_KEY": self.SECRET_KEY,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
        }
        weak = [
            name
            for name, value in unsafe_values.items()
            if not value or "change-me" in value.lower() or len(value) < 32
        ]
        if weak:
            joined = ", ".join(weak)
            raise RuntimeError(f"Unsafe production secret configuration: {joined}")

        if self.APP_DEBUG:
            raise RuntimeError("APP_DEBUG must be false in production")

        if "*" in self.cors_origins_list:
            raise RuntimeError("Wildcard CORS origins are not allowed in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
