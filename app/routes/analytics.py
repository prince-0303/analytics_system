from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Event
from app.schemas import AnalyticsResponse
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    event: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to")
):
    query = db.query(Event)

    # Apply filters
    if event:
        query = query.filter(Event.event.ilike(f"%{event}%"))
    if from_date:
        query = query.filter(Event.timestamp >= from_date)
    if to_date:
        query = query.filter(Event.timestamp <= to_date)

    all_events = query.all()

    # Total events
    total_events = len(all_events)

    # Events per user
    events_per_user = {}
    for e in all_events:
        events_per_user[e.user_id] = events_per_user.get(e.user_id, 0) + 1

    # Most active users
    most_active_users = sorted(
        [{"user_id": uid, "count": count} for uid, count in events_per_user.items()],
        key=lambda x: x["count"],
        reverse=True
    )

    return AnalyticsResponse(
        total_events=total_events,
        events_per_user=events_per_user,
        most_active_users=most_active_users
    )