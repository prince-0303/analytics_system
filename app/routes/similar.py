from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event
from app.services.vector_search import find_similar_users

router = APIRouter()

@router.get("/similar-users")
def get_similar_users(
    userId: str = Query(..., description="User ID to find similar users for"),
    n_results: int = Query(5, description="Number of similar users to return"),
    db: Session = Depends(get_db)
):
    # Get all unique user IDs from PostgreSQL
    all_user_ids = [
        row.user_id for row in db.query(Event.user_id).distinct().all()
    ]

    if userId not in all_user_ids:
        raise HTTPException(status_code=404, detail="User not found")

    similar = find_similar_users(
        user_id=userId,
        all_user_ids=all_user_ids,
        n_results=n_results
    )

    if not similar:
        return {"message": "No similar users found", "similar_users": []}

    return {"user_id": userId, "similar_users": similar}