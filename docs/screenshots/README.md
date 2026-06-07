# NexusOps AI Screenshots

These screenshots were generated from the local Docker Compose stack using demo infrastructure, telemetry, incidents, Terraform findings, and cost optimization data.

| Page | Screenshot |
|---|---|
| Dashboard | ![Dashboard](dashboard.png) |
| Infrastructure | ![Infrastructure](infrastructure.png) |
| Incidents | ![Incidents](incidents.png) |
| Security | ![Security](security.png) |
| Cost Optimization | ![Cost Optimization](cost-optimization.png) |
| AI Investigation | ![AI Investigation](ai-investigation.png) |

To regenerate screenshots, start Chrome with remote debugging and run:

```bash
node scripts/capture-screenshots.mjs "$TOKEN" "demo@nexusops.ai" docs/screenshots
```
