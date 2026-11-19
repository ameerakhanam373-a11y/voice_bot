"""Index PDF files from docs/ into the local Qdrant database."""
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models

from config import DOCS_DIR, EMBEDDING_MODEL, QDRANT_COLLECTION, QDRANT_PATH


def main() -> None:
    files = sorted(DOCS_DIR.glob("*.pdf"))
    if not files:
        raise SystemExit(f"No PDFs found in {DOCS_DIR}. Add Academy documents first.")
    print("Loading documents...")
    documents = []
    for path in files:
        documents.extend(PyPDFLoader(str(path)).load())
    print("Splitting documents...")
    chunks = RecursiveCharacterTextSplitter(chunk_size=850, chunk_overlap=120).split_documents(documents)
    print("Generating embeddings...")
    # Prefer an already-downloaded model so ingestion works even if Hugging Face
    # is temporarily unreachable. If there is no cache yet, download it normally.
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu", "local_files_only": True},
        encode_kwargs={"normalize_embeddings": True},
    )
    try:
        vector_size = len(embeddings.embed_query("dimension check"))
    except Exception:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        vector_size = len(embeddings.embed_query("dimension check"))
    print("Creating Qdrant collection...")
    QDRANT_PATH.mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=str(QDRANT_PATH))
    if client.collection_exists(QDRANT_COLLECTION):
        client.delete_collection(QDRANT_COLLECTION)
    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
    )
    print("Inserting documents...")
    # Fresh collection replacement makes repeated runs deterministic and avoids duplicate chunks.
    store = Qdrant(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embeddings=embeddings,
    )
    ids = [
        str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            d.metadata.get("source", "") + str(d.metadata.get("page", "")) + d.page_content,
        ))
        for d in chunks
    ]
    store.add_documents(chunks, ids=ids)
    inserted = client.count(QDRANT_COLLECTION, exact=True).count
    client.close()
    if inserted != len(chunks):
        raise RuntimeError(f"Expected {len(chunks)} indexed chunks, but Qdrant contains {inserted}.")
    print(f"Ingestion completed. Indexed {len(chunks)} chunks from {len(files)} PDFs.")


if __name__ == "__main__":
    main()
