import chromadb
from chromadb.config import Settings


client = chromadb.PersistentClient(path="./chroma_store") # saves vectors to disk locally

""" 
event creates a collection if not exists, reuses if it have
uses cosine similarity to compare vectors
"""
collections = client.get_or_create_collection(name="events", metadata={"hnsw:space": "cosine"})