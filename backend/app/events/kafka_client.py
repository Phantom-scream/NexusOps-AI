"""
NexusOps AI — Kafka/Redpanda Event Streaming Client
Async Kafka producer for platform event bus
"""
from typing import Any, Dict, Optional

import json
import structlog
from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger = structlog.get_logger(__name__)


class KafkaManager:
    """
    Manages the Kafka/Redpanda producer lifecycle.
    Used to publish infrastructure events to the event bus.
    """

    def __init__(self):
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Start the Kafka producer."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type="gzip",
            )
            await self._producer.start()
            logger.info("Kafka producer started", brokers=settings.KAFKA_BOOTSTRAP_SERVERS)
        except Exception as exc:
            logger.warning("Kafka producer failed to start (non-fatal)", error=str(exc))
            self._producer = None

    async def stop(self) -> None:
        """Gracefully shut down the producer."""
        if self._producer:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def publish(
        self,
        topic: str,
        event: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """
        Publish an event to a Kafka topic.
        Silently fails if Kafka is unavailable (non-blocking degradation).
        """
        if not self._producer:
            logger.debug("Kafka unavailable, skipping event publish", topic=topic)
            return

        try:
            await self._producer.send_and_wait(topic, value=event, key=key)
            logger.debug("Event published", topic=topic, key=key)
        except Exception as exc:
            logger.error("Failed to publish Kafka event", topic=topic, error=str(exc))

    async def publish_incident_event(
        self,
        incident_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """Publish an incident lifecycle event."""
        from datetime import datetime, timezone
        event = {
            "event_type": event_type,
            "incident_id": incident_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        await self.publish(settings.KAFKA_TOPIC_INCIDENTS, event, key=incident_id)

    async def publish_cluster_event(
        self,
        cluster_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a cluster lifecycle event."""
        from datetime import datetime, timezone
        event = {
            "event_type": event_type,
            "cluster_id": cluster_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        await self.publish(settings.KAFKA_TOPIC_EVENTS, event, key=cluster_id)


kafka_manager = KafkaManager()
