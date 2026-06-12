from fastapi import FastAPI
from app.database import Base, engine
from app.routes import track, analytics, search, similar

app = FastAPI(
    title="User analytics + Semantic Search System",
    description="Tracks user events, provides analytics, and enables AI-powered semantic search"
)

Base.metadata.create_all(bind=engine)

app.include_router(track.router)
app.include_router(analytics.router)
app.include_router(search.router)
app.include_router(similar.router)

@app.get("/")
def root():
    return{"message": "Analytics System is Working"}