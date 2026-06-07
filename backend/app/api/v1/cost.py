"""
NexusOps AI — Cost Optimization API
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.cost_recommendation import CostRecommendation
from app.repositories.base import BaseRepository

router = APIRouter()


@router.get("/recommendations")
async def list_recommendations(
    cluster_id: str | None = Query(default=None),
    optimization_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """List cost optimization recommendations."""
    repo = BaseRepository(model=CostRecommendation, session=db)
    filters = {}
    if cluster_id:
        filters["cluster_id"] = cluster_id
    if optimization_type:
        filters["optimization_type"] = optimization_type

    skip = (page - 1) * page_size
    recs = await repo.get_all(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    return {
        "items": [
            {
                "id": r.id,
                "cluster_name": r.cluster_name,
                "namespace": r.namespace,
                "workload_name": r.workload_name,
                "optimization_type": r.optimization_type,
                "title": r.title,
                "estimated_monthly_savings_usd": r.estimated_monthly_savings_usd,
                "priority": r.priority,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in recs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/dashboard")
async def get_cost_dashboard(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """Get cost optimization dashboard summary."""
    repo = BaseRepository(model=CostRecommendation, session=db)
    all_recs = await repo.get_all(limit=1000)

    total_savings = sum(
        r.estimated_monthly_savings_usd or 0
        for r in all_recs
        if r.status == "open"
    )

    by_type = {}
    for r in all_recs:
        by_type[r.optimization_type] = by_type.get(r.optimization_type, 0) + 1

    return {
        "total_open_recommendations": len([r for r in all_recs if r.status == "open"]),
        "estimated_monthly_savings_usd": round(total_savings, 2),
        "recommendations_by_type": by_type,
        "top_opportunities": [
            {
                "id": r.id,
                "title": r.title,
                "cluster_name": r.cluster_name,
                "estimated_monthly_savings_usd": r.estimated_monthly_savings_usd,
            }
            for r in sorted(all_recs, key=lambda x: x.estimated_monthly_savings_usd or 0, reverse=True)[:5]
        ],
    }
