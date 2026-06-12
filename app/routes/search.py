from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event
from app.schemas import SearchResult
from app.services.vector_search import search_similar_events, hybrid_search
from app.services.embedding import rerank_results
from typing import Optional
from uuid import UUID

router = APIRouter()

@router.get("/search", response_model=list[SearchResult])
def semantic_search(
    query: str = Query(..., description="Plain English search query"),
    n_results: int = Query(5, description="Number of results to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: Optional[str] = Query(None, description="Filter by page"),
    hybrid: bool = Query(False, description="Enable hybrid search"),
    rerank: bool = Query(False, description="Enable re-ranking"),
    db: Session = Depends(get_db)
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if hybrid:
        matches = hybrid_search(
            query=query,
            db=db,
            n_results=n_results,
            user_id=user_id,
            page=page
        )
        score_key = "combined_score"
    else:
        matches = search_similar_events(
            query=query,
            n_results=n_results,
            user_id=user_id,
            page=page
        )
        score_key = "similarity_score"

    if not matches:
        return []

    # Fetch full event details from PostgreSQL
    enriched = []
    for match in matches:
        event = db.query(Event).filter(Event.id == UUID(match["id"])).first()
        if event:
            enriched.append({
                "id": match["id"],
                "event": event.event,
                "user_id": event.user_id,
                "event_metadata": event.event_metadata,
                "timestamp": event.timestamp,
                score_key: match[score_key]
            })

    # Apply re-ranking 
    if rerank:
        enriched = rerank_results(query=query, candidates=enriched)
        score_key = "rerank_score"

    results = []
    for item in enriched:
        results.append(SearchResult(
            id=item["id"],
            user_id=item["user_id"],
            event=item["event"],
            metadata=item["event_metadata"],
            timestamp=item["timestamp"],
            similarity_score=item.get(score_key, 0.0)
        ))

    return results