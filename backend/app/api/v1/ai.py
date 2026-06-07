"""
NexusOps AI — AI Investigation API
Real-time and async AI investigation endpoints with WebSocket streaming
"""
import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.incident_analyzer import IncidentInvestigationEngine
from app.ai.rag_pipeline import RAGPipeline
from app.core.database import get_db
from app.core.security import CurrentUser, decode_token, get_current_user, require_operator
from app.schemas.incident import AIInvestigateRequest, AIInvestigateResponse

router = APIRouter()

rag_pipeline = RAGPipeline()
investigation_engine = IncidentInvestigationEngine(rag_pipeline=rag_pipeline)


@router.post("/investigate", response_model=AIInvestigateResponse)
async def investigate_infrastructure(
    request: AIInvestigateRequest,
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(require_operator),
):
    """
    Synchronous AI incident investigation.
    Analyzes cluster telemetry and returns structured root cause analysis.
    """
    from app.models.cluster import Cluster
    from app.repositories.cluster_repository import ClusterRepository
    from app.services.cluster_service import ClusterService

    service = ClusterService(
        repository=ClusterRepository(model=Cluster, session=db)
    )
    cluster = await service.get_cluster(request.cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    result = await investigation_engine.investigate(
        cluster_name=cluster.name,
        query=request.query,
        namespace=request.namespace,
        workload=request.workload,
        context_window_minutes=request.context_window_minutes,
    )

    return AIInvestigateResponse(
        incident_id=None,
        severity=result.get("severity", "medium"),
        root_cause=result.get("root_cause", ""),
        contributing_factors=result.get("contributing_factors", []),
        remediation=result.get("remediation", {}),
        confidence=result.get("confidence", 0.0),
        analysis_detail=result.get("root_cause_detail", ""),
        tokens_used=result.get("tokens_used"),
    )


@router.post("/query")
async def rag_infrastructure_query(
    query: str,
    _: CurrentUser = Depends(get_current_user),
):
    """
    RAG-powered infrastructure Q&A.
    Searches indexed manifests, incidents, and runbooks to answer questions.
    """
    result = await rag_pipeline.rag_query(query)
    return {
        "query": query,
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "tokens_used": result.get("tokens_used"),
    }


@router.websocket("/stream/{cluster_id}")
async def ai_investigation_stream(
    websocket: WebSocket,
    cluster_id: str,
    token: str | None = None,
):
    """
    WebSocket endpoint for streaming AI investigation in real-time.
    Client connects and sends queries; server streams token-by-token responses.
    """
    # Validate token
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        decode_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            query = message.get("query", "")

            if not query:
                continue

            # Stream AI response token-by-token
            await websocket.send_json({
                "type": "analysis_start",
                "cluster_id": cluster_id,
                "query": query,
            })

            full_response = ""
            async for token_chunk in investigation_engine.stream_investigation(
                cluster_id=cluster_id,
                query=query,
            ):
                full_response += token_chunk
                await websocket.send_json({
                    "type": "token",
                    "content": token_chunk,
                })

            await websocket.send_json({
                "type": "analysis_complete",
                "full_response": full_response,
            })

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
        await websocket.close()
