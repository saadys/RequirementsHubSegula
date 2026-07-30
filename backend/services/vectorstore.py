import os
import chromadb
import google.generativeai as genai
from chromadb import EmbeddingFunction, Documents, Embeddings
from backend import config

class GoogleGeminiEmbeddingFunction(EmbeddingFunction):
    """Custom ChromaDB Embedding Function that calls Google's Generative AI API with key rotation and fallback."""
    def __call__(self, input: Documents) -> Embeddings:
        # Build list of keys to try
        keys_to_try = []
        if config.GEMINI_API_KEY_1:
            keys_to_try.append(config.GEMINI_API_KEY_1)
        if config.GEMINI_API_KEY_2:
            keys_to_try.append(config.GEMINI_API_KEY_2)

        if not keys_to_try:
            raise ValueError("No Gemini API keys configured in environment variables.")

        last_error = None
        for key in keys_to_try:
            try:
                # Re-configure client with the current key
                genai.configure(api_key=key)
                
                print(f"[Embeddings] Attempting to use primary model: {config.EMBEDDING_MODEL}")
                response = genai.embed_content(
                    model=config.EMBEDDING_MODEL,
                    content=input,
                    task_type="retrieval_document"
                )
                print(f"[Embeddings] Successfully embedded with model: {config.EMBEDDING_MODEL}")
                return response["embedding"]
            except Exception as e:
                last_error = e
                err_msg = str(e).lower()
                # If the error is model not found (404), try fallback models with the current key
                if "not found" in err_msg or "not supported" in err_msg:
                    print(f"[Embeddings] Primary model {config.EMBEDDING_MODEL} failed. Trying fallbacks...")
                    for fallback in ["models/gemini-embedding-001", "models/gemini-embedding-2"]:
                        try:
                            print(f"[Embeddings] Attempting fallback model: {fallback}")
                            response = genai.embed_content(
                                model=fallback,
                                content=input,
                                task_type="retrieval_document"
                            )
                            print(f"[Embeddings] Successfully embedded with fallback model: {fallback}")
                            return response["embedding"]
                        except Exception as fe:
                            last_error = fe
                # If key expired or failed, proceed to next key
                print(f"[Embeddings] API Key failed or encountered error: {e}. Moving to next key...")
                continue

        # If all keys and fallbacks failed, raise the last exception
        raise last_error


# Fallback path if CHROMA_PERSIST_DIR is not yet in config.py
persist_dir = getattr(config, "CHROMA_PERSIST_DIR", os.path.join(config.DATA_DIR, "chroma"))

# Initialize ChromaDB persistent client
client = chromadb.PersistentClient(path=persist_dir)

def get_collection():
    """Gets or creates the ChromaDB collection using Google's embedding function."""
    embedding_function = GoogleGeminiEmbeddingFunction()
    return client.get_or_create_collection(
        name=config.CHROMA_COLLECTION_NAME,
        embedding_function=embedding_function
    )