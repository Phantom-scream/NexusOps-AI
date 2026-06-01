"""Tests — Infrastructure discovery providers and topology APIs."""

from httpx import AsyncClient
import pytest

from app.infrastructure.providers.demo import DemoProvider
from app.models.cluster import Cluster
from app.repositories.cluster_repository import ClusterRepository
from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService


async def _get_token(client: AsyncClient) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "infra_test@nexusops.ai",
            "username": "infrauser",
            "password": "Password1",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "infra_test@nexusops.ai",
            "password": "Password1",
        },
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_demo_provider_ingests_shared_domain_model(db_session):
    service = InfrastructureDiscoveryService(
        repository=ClusterRepository(model=Cluster, session=db_session)
    )
    snapshot = DemoProvider().discover()

    cluster = await service.ingest_snapshot(snapshot)
    await db_session.flush()

    repo = ClusterRepository(model=Cluster, session=db_session)
    topology_cluster = await repo.get_with_topology(cluster.id)

    assert topology_cluster is not None
    assert topology_cluster.provider == "demo"
    assert topology_cluster.namespace_count > 0
    assert topology_cluster.deployment_count > 0
    assert topology_cluster.pod_count > 0
    assert len(topology_cluster.pods) == topology_cluster.pod_count
    assert len(topology_cluster.services) == topology_cluster.service_count


@pytest.mark.asyncio
async def test_demo_generate_and_topology_api(client: AsyncClient):
    token = await _get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    generated = await client.post("/api/v1/demo/generate", headers=headers)
    assert generated.status_code == 200
    clusters = generated.json()
    assert len(clusters) >= 1

    cluster_id = clusters[0]["id"]
    topology = await client.get(f"/api/v1/clusters/{cluster_id}/topology", headers=headers)
    assert topology.status_code == 200
    body = topology.json()
    assert body["root"]["type"] == "cluster"
    assert body["root"]["children"]

    pods = await client.get(f"/api/v1/clusters/{cluster_id}/pods", headers=headers)
    assert pods.status_code == 200
    assert len(pods.json()) > 0
