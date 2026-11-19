"""Local PDF retrieval using sentence-transformers and embedded Qdrant."""
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import QDRANT_COLLECTION, QDRANT_PATH, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        # Use the model downloaded during ingestion. Avoid a network metadata
        # lookup for every query so retrieval also works offline.
        model_kwargs={"device": "cpu", "local_files_only": True},
        encode_kwargs={"normalize_embeddings": True},
    )


def _store():
    from langchain_community.vectorstores import Qdrant
    return Qdrant.from_existing_collection(
        embedding=_embeddings(),
        collection_name=QDRANT_COLLECTION,
        path=str(QDRANT_PATH),
    )


def search_documents(query: str, limit: int = 4) -> list[dict[str, Any]]:
    """Return matching chunks with source, page, and similarity score."""
    if not query or not query.strip():
        return []
    store = _store()
    hits = store.similarity_search_with_score(query.strip(), k=limit)
    results = []
    for doc, score in hits:
        source = Path(str(doc.metadata.get("source", "unknown"))).name
        page = doc.metadata.get("page")
        results.append({
            "text": doc.page_content,
            "source": source,
            "page": int(page) + 1 if isinstance(page, int) else page,
            "score": float(score),
        })
    return results


def knowledge_base_status() -> tuple[bool, str]:
    """Check whether the local vector collection is available."""
    if not QDRANT_PATH.exists():
        return False, "Knowledge base not indexed"
    try:
        # Opening Qdrant alone does not confirm that the embedding model can
        # encode a query. Warm it here so this status reflects actual RAG readiness.
        _embeddings().embed_query("status check")
        store = _store()
        points = store.client.count(QDRANT_COLLECTION, exact=True).count
        if points == 0:
            return False, "Qdrant collection is empty. Stop Streamlit, run ingest.py, then restart the app."
        return True, "Local Qdrant ready"
    except Exception:
        return False, "Local embeddings unavailable. Run ingest.py once with internet access, then restart the app."
