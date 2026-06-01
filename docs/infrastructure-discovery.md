# Infrastructure Discovery

NexusOps AI Phase 4 introduces a provider-based infrastructure discovery engine.

## Provider Architecture

All infrastructure sources emit the same normalized `InfrastructureSnapshot` and are ingested into the same PostgreSQL domain model.

Providers:

- `KubernetesProvider`: discovers live Kubernetes resources through kubeconfig, in-cluster config, Minikube, or Kind.
- `DemoProvider`: generates realistic enterprise Kubernetes infrastructure for local development and demonstrations.

The API and frontend do not know which provider created the records. They read persisted clusters, namespaces, deployments, pods, services, nodes, and topology.

## Persisted Resources

The infrastructure model stores:

- `Cluster`
- `ClusterNode`
- `KubernetesNamespace`
- `KubernetesWorkload` for deployments and other workload controllers
- `KubernetesReplicaSet`
- `KubernetesPod`
- `KubernetesService`

Sync replaces the discovered child topology for a cluster with the latest provider snapshot.

## API Surface

Cluster and topology APIs:

- `GET /api/v1/clusters`
- `GET /api/v1/clusters/{id}`
- `GET /api/v1/clusters/{id}/nodes`
- `GET /api/v1/clusters/{id}/namespaces`
- `GET /api/v1/clusters/{id}/deployments`
- `GET /api/v1/clusters/{id}/pods`
- `GET /api/v1/clusters/{id}/services`
- `GET /api/v1/clusters/{id}/replicasets`
- `GET /api/v1/clusters/{id}/topology`
- `POST /api/v1/clusters/{id}/sync`

Demo mode:

- `POST /api/v1/demo/generate`

## Demo Mode

Demo mode creates multiple realistic clusters:

- `prod-us-east-1`
- `staging-central`
- `platform-monitoring`

The generated topology includes namespaces, deployments, ReplicaSets, pods, services, nodes, healthy workloads, degraded workloads, and crash-looping pods. It uses the same models and APIs as Kubernetes discovery.

## Frontend

The Infrastructure page now uses React Query and backend APIs. It no longer renders infrastructure from frontend mock data.

It displays:

- cluster inventory
- node and namespace summaries
- deployments
- pods
- services
- topology tree: Cluster → Namespace → Deployment → Pod

When no infrastructure exists, use **Generate Demo Infrastructure** to populate the same backend domain model used by live Kubernetes discovery.
