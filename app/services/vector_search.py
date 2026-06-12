from app.chromadb_client import collections
from app.services.embedding import generate_embedding


def save_embedding(event_id: str, event_text: str, user_id: str, timestamp: str):
    embedding = generate_embedding(event_text)

    collections.add(
        ids=[event_id],
        embeddings=[embedding],
        documents=[event_text],
        metadatas=[{"user_id": user_id, "timestamp": timestamp}]        
    )

def search_similar_events(query: str, n_results: int = 5, user_id: str = None, page: str = None) -> list[dict]:
    query_embedding = generate_embedding(query)

    # Build ChromaDB where filter
    where_filter = {}
    if user_id and page:
        where_filter = {"$and": [{"user_id": user_id}, {"page": page}]}
    elif user_id:
        where_filter = {"user_id": user_id}
    elif page:
        where_filter = {"page": page}

    results = collections.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter if where_filter else None
    )

    matches = []
    for i, event_id in enumerate(results["ids"][0]):
        matches.append({
            "id": event_id,
            "event": results["documents"][0][i],
            "similarity_score": 1 - results["distances"][0][i],
            "metadata": results["metadatas"][0][i]
        })
    return matches

def get_user_embedding(user_id: str) -> list[float] | None:
    results = collections.get(
        where={"user_id": user_id},
        include=["embeddings", "metadatas"]
    )
    embeddings = results["embeddings"]
    if embeddings is None or len(embeddings) == 0:
        return None

    # Convert to plain python lists to avoid numpy issues
    embeddings = [list(e) for e in embeddings]
    avg = [sum(col) / len(col) for col in zip(*embeddings)]
    return avg

def find_similar_users(user_id: str, all_user_ids: list[str], n_results: int = 5) -> list[dict]:
    target_embedding = get_user_embedding(user_id)
    if not target_embedding:
        return []

    similar = []
    for uid in all_user_ids:
        if str(uid) == str(user_id):  # skip self
            continue
        other_embedding = get_user_embedding(uid)
        if not other_embedding:
            continue

        dot_product = sum(a * b for a, b in zip(target_embedding, other_embedding))
        mag_a = sum(a ** 2 for a in target_embedding) ** 0.5
        mag_b = sum(b ** 2 for b in other_embedding) ** 0.5
        score = dot_product / (mag_a * mag_b) if mag_a and mag_b else 0
        similar.append({"user_id": uid, "similarity_score": round(score, 4)})

    similar.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar[:n_results]

def hybrid_search(query: str, db, n_results: int = 5, user_id: str = None, page: str = None) -> list[dict]:
    # Vector search from ChromaDB
    vector_matches = search_similar_events(
        query=query,
        n_results=n_results,
        user_id=user_id,
        page=page
    )
    vector_scores = {m["id"]: m["similarity_score"] for m in vector_matches}

    # Keyword search from PostgreSQL
    from app.models import Event
    keyword_query = db.query(Event).filter(Event.event.ilike(f"%{query}%"))
    if user_id:
        keyword_query = keyword_query.filter(Event.user_id == user_id)
    if page:
        keyword_query = keyword_query.filter(
            Event.event_metadata["page"].astext == page
        )
    keyword_results = keyword_query.limit(n_results).all()
    keyword_ids = {str(e.id) for e in keyword_results}

    # Merge both result sets
    all_ids = set(vector_scores.keys()) | keyword_ids

    merged = []
    for event_id in all_ids:
        vector_score = vector_scores.get(event_id, 0.0)
        keyword_score = 1.0 if event_id in keyword_ids else 0.0

        # Combined score: 70% vector + 30% keyword
        combined_score = (0.7 * vector_score) + (0.3 * keyword_score)
        merged.append({
            "id": event_id,
            "combined_score": round(combined_score, 4),
            "vector_score": round(vector_score, 4),
            "keyword_score": keyword_score
        })

    merged.sort(key=lambda x: x["combined_score"], reverse=True)
    return merged[:n_results]