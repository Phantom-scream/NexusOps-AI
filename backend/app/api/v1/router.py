"""
NexusOps AI — API v1 Router
Central router that registers all API sub-routers
"""
from fastapi import APIRouter

from app.api.v1 import ai, auth, clusters, cost, demo, incidents, security

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(clusters.router, prefix="/clusters", tags=["Clusters"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(security.router, prefix="/security", tags=["Security"])
api_router.include_router(cost.router, prefix="/cost", tags=["Cost Optimization"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Investigation"])
api_router.include_router(demo.router, prefix="/demo", tags=["Demo Infrastructure"])
