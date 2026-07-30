import os
import chromadb
from backend import config

# Fallback path if CHROMA_PERSIST_DIR is not yet in config.py
persist_dir = getattr(config, "CHROMA_PERSIST_DIR", os.path.join(config.DATA_DIR, "chroma"))

# Initialize ChromaDB persistent client
client = chromadb.PersistentClient(path=persist_dir)

def get_collection():
    """Gets or creates the ChromaDB collection using the default embedding function."""
    return client.get_or_create_collection(
        name=config.CHROMA_COLLECTION_NAME
    )