from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event
from app.schemas import SearchResult
from app.services.vector_search import search_similar_events
from uuid import UUID

router = APIRouter()

@router.get("/search", response_model=list[SearchResult])
def semantic_search(
    query: str = Query(..., description="Plain English search query"),
    n_results: int = Query(5, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Step 1: Search ChromaDB for similar events
    matches = search_similar_events(query=query, n_results=n_results)

    if not matches:
        return []

    # Step 2: Fetch full event details from PostgreSQL
    results = []
    for match in matches:
        event = db.query(Event).filter(Event.id == UUID(match["id"])).first()
        if event:
            results.append(SearchResult(
                id=event.id,
                user_id=event.user_id,
                event=event.event,
                metadata=event.event_metadata,
                timestamp=event.timestamp,
                similarity_score=match["similarity_score"]
            ))

    return results