"""ChromaDB vector store with Ollama or OpenAI embeddings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import CHROMA_DIR, get_openai_api_key, get_ollama_base_url, get_ollama_embedding_model


def get_embeddings():
    """Get embeddings: OpenAI if key set, else Ollama, else fallback."""
    api_key = get_openai_api_key()
    if api_key:
        try:
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(openai_api_key=api_key, model="text-embedding-3-small")
        except ImportError:
            pass

    try:
        from langchain_community.embeddings import OllamaEmbeddings

        return OllamaEmbeddings(
            base_url=get_ollama_base_url(),
            model=get_ollama_embedding_model(),
        )
    except Exception:
        pass

    return _fallback_embeddings()


def _fallback_embeddings():
    """Fallback: use simple hash-based pseudo-embeddings if Ollama unavailable."""
    class SimpleEmbeddings:
        def embed_documents(self, texts):
            import hashlib
            return [[hash(t[:500]) % 1000 / 1000.0 for _ in range(384)] for t in texts]

        def embed_query(self, text):
            import hashlib
            return [hash(text[:500]) % 1000 / 1000.0 for _ in range(384)]

    return SimpleEmbeddings()


def get_vector_store(collection_name: str = "property_docs"):
    """Get or create ChromaDB collection."""
    import chromadb
    from chromadb.config import Settings

    embeddings = get_embeddings()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR), settings=Settings(anonymized_telemetry=False))

    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    return collection, embeddings


def add_documents(collection, embeddings, chunks: list[str], doc_id: str = "upload"):
    """Add document chunks to vector store."""
    if not chunks:
        return
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    embeds = embeddings.embed_documents(chunks)
    try:
        collection.upsert(ids=ids, documents=chunks, embeddings=embeds, metadatas=[{"doc_id": doc_id}] * len(chunks))
    except Exception:
        collection.add(ids=ids, documents=chunks, embeddings=embeds, metadatas=[{"doc_id": doc_id}] * len(chunks))


def query_documents(collection, embeddings, query: str, n_results: int = 5) -> list[str]:
    """Query vector store and return relevant chunks."""
    query_embedding = embeddings.embed_query(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
    if results and results.get("documents"):
        return results["documents"][0]
    return []
