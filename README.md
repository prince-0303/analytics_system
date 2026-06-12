# User Analytics + Semantic Search System

A backend system that tracks user events, provides analytics, and enables AI-powered semantic search using embeddings.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | FastAPI | Async-friendly, ideal for I/O heavy embedding generation, auto-generates Swagger docs |
| Database | PostgreSQL | Structured queries, date range filters, aggregations |
| Vector Store | ChromaDB | Lightweight, persistent, local — no external service needed |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Free, local, 384-dim vectors, no API key |
| Re-ranking | cross-encoder/ms-marco-MiniLM-L-6-v2 | Handles negation and context — improves accuracy |

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone 
cd analytics_system
```

### 2. Create and activate virtual environment
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/analytics_db
```
> If your password contains `@`, replace it with `%40`

### 5. Create the database
Create a PostgreSQL database named `analytics_db` using pgAdmin or:
```bash
createdb analytics_db
```

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

The API will be live at `http://127.0.0.1:8000`
Interactive docs available at `http://127.0.0.1:8000/docs`

> Note: First startup downloads two AI models (~180MB total). Subsequent startups are fast as models are cached locally.

---

## API Documentation

### POST /track
Track a user event. Saves to PostgreSQL and generates + stores an embedding in ChromaDB.

**Request:**
```json
{
  "userId": "user_1",
  "event": "user viewed pricing page",
  "metadata": { "page": "/pricing" },
  "timestamp": "2026-06-11T10:00:00Z"
}
```

**Response:**
```json
{
  "id": "24dbbb9a-281c-49f3-a73a-38ad8249d03d",
  "message": "Event tracked successfully"
}
```

---

### GET /analytics
Get event analytics with optional filters.

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `event` | string | Filter by event text (partial match) |
| `from` | datetime | Start date |
| `to` | datetime | End date |

**Example:** `GET /analytics?event=pricing&from=2026-01-01`

**Response:**
```json
{
  "total_events": 5,
  "events_per_user": {
    "user_1": 2,
    "user_2": 2,
    "user_3": 1
  },
  "most_active_users": [
    { "user_id": "user_1", "count": 2 },
    { "user_id": "user_2", "count": 2 },
    { "user_id": "user_3", "count": 1 }
  ]
}
```

---

### GET /search
Semantic search over events using natural language. Supports metadata filtering, hybrid search, and re-ranking.

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | Plain English search query |
| `n_results` | integer | 5 | Number of results |
| `user_id` | string | null | Filter by user |
| `page` | string | null | Filter by page |
| `hybrid` | boolean | false | Enable hybrid search |
| `rerank` | boolean | false | Enable re-ranking |

**Example:** `GET /search?query=purchase intent&rerank=true`

**Response:**
```json
[
  {
    "id": "529ef6e4-c166-4dfe-85e6-0e88d9b76f82",
    "user_id": "user_1",
    "event": "user clicked the buy button",
    "metadata": { "page": "/checkout" },
    "timestamp": "2026-06-11T22:27:08.095270",
    "similarity_score": 0.5697
  }
]
```

---

### GET /similar-users
Find users with similar behavior patterns using vector similarity.

**Query Parameters:**
| Parameter | Type | Default | Description |
|---|---|---|---|
| `userId` | string | required | User to compare against |
| `n_results` | integer | 5 | Number of similar users |

**Example:** `GET /similar-users?userId=user_1`

**Response:**
```json
{
  "user_id": "user_1",
  "similar_users": [
    { "user_id": "user_2", "similarity_score": 0.8023 },
    { "user_id": "user_3", "similarity_score": 0.3026 }
  ]
}
```

---

## Design Decisions

### Why FastAPI?
FastAPI is async-friendly and ideal for AI workloads involving embedding generation which is I/O heavy. It also auto-generates interactive Swagger documentation making testing straightforward.

### Why PostgreSQL?
Analytics queries require structured filtering — by event type, date ranges, and aggregations. PostgreSQL handles these efficiently with indexes on `user_id` and `timestamp` columns.

### Why ChromaDB?
ChromaDB is a lightweight persistent vector store that runs locally without any external service or API key. It was chosen over Pinecone (requires cloud account) and FAISS (no built-in persistence) for simplicity in a local development environment.

### Why sentence-transformers?
The `all-MiniLM-L6-v2` model runs entirely locally, requires no API key, and produces high-quality 384-dimensional embeddings. It is the industry standard for lightweight semantic search.

### Two Database Sync Strategy
PostgreSQL and ChromaDB have no shared transaction. Consistency is handled manually:
1. Save event to PostgreSQL → get UUID
2. Generate embedding → save to ChromaDB with same UUID
3. If ChromaDB fails → delete PostgreSQL row → return error

Either both databases have the data or neither does.

### Search Enhancements (Beyond Requirements)

**Metadata Filtering:** Scopes ChromaDB search to a specific user or page using ChromaDB's native `where` filter. Useful for per-user analysis — "what did user_1 search for on the pricing page?"

**Hybrid Search:** Combines vector search (meaning) with PostgreSQL keyword search (exact match) using a 70/30 weighted score. Improves accuracy when exact terms appear in the data.

**Re-ranking:** Uses a CrossEncoder model that reads query and event together as a pair — unlike embeddings which score them separately. This handles negation correctly. Example: "didn't buy" with pure vector search returns "clicked buy button" as #1. With re-ranking, "user left without purchasing" correctly ranks #1.

### Scalability Considerations
- `user_id` and `timestamp` columns are indexed for fast analytics queries
- Both AI models load once at startup and stay in memory
- For production scale, ChromaDB can be replaced with Pinecone or Weaviate
- Similar-users endpoint computes similarity in-memory — for large user bases this should move to a pre-computed scheduled job
