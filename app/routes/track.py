from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event
from app.schemas import TrackRequest, TrackResponse
from app.services.vector_search import save_embedding
from datetime import datetime, timezone
import uuid

router = APIRouter()

@router.post("/track", response_model=TrackResponse)
def track_event(payload: TrackRequest, db: Session = Depends(get_db)):

    event_id = uuid.uuid4()
    timestamp = payload.timestamp or datetime.now(timezone.utc)

    # save to postgres
    db_event = Event(
        id=event_id,
        user_id=payload.userId,
        event=payload.event,
        event_metadata=payload.metadata,
        timestamp=timestamp
    )

    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    try:
        save_embedding(
            event_id=str(event_id),
            event_text=payload.event,
            user_id=payload.userId,
            timestamp=str(timestamp)
        )
    except Exception as e:
        db.delete(db_event)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Vector store error: {str(e)}")
    return TrackResponse(id=event_id, message="Event tracked successfully")