from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def generate_embedding(text: str) -> list[float]:
    embedding = model.encode(text)
    return embedding.tolist()

def rerank_results(query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []

    pairs = [[query, c["event"]] for c in candidates]
    scores = reranker.predict(pairs)

    # Normalize scores to 0-1 range using sigmoid
    normalized = [1 / (1 + float(np.exp(-s))) for s in scores]

    for i, candidate in enumerate(candidates):
        candidate["rerank_score"] = round(normalized[i], 4)

    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    return candidates