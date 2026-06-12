from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
import uuid

class TrackRequest(BaseModel):
    userId: str
    event: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class TrackResponse(BaseModel):
    id: uuid.UUID
    message: str

class EventOut(BaseModel):
    id: uuid.UUID
    user_id: str
    event: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    total_events: int
    events_per_user: Dict[str, int]
    most_active_users: List[Dict[str, Any]]

class SearchResult(BaseModel):
    id: uuid.UUID
    user_id: str
    event: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    similarity_score: Optional[float] = None