from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# =========================
# Configuración global
# =========================

CHROMA_DIR = "chroma_db"

# Modelo de embeddings
# all-MiniLM-L6-v2 es rápido y suficiente para PDFs largos
model = SentenceTransformer("all-MiniLM-L6-v2")

# Cliente Chroma persistente
chroma_client = chromadb.Client(
    Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False
    )
)

# Colección principal
collection = chroma_client.get_or_create_collection(
    name="deeppdf_docs"
)

# =========================
# Utilidades de chunking
# =========================

def chunk_text(text, chunk_size=500, overlap=100):
    """
    Divide el texto en chunks y calcula páginas aproximadas.
    NOTA: overlap aún no se aplica (dejado para futura mejora).
    """
    chunks = []
    chunk_metadata = []

    chars_per_page = 2000  # Estimación aproximada de caracteres por página

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]

        # Omitir fragmentos demasiado pequeños o irrelevantes
        if len(chunk.strip()) < 50:
            continue

        chunks.append(chunk)

        approx_page = (i // chars_per_page) + 1

        chunk_metadata.append({
            "chunk_index": len(chunks) - 1,
            "approx_page": approx_page,
            "char_start": i,
            "char_end": min(i + chunk_size, len(text))
        })

    return chunks, chunk_metadata

# =========================
# Almacenamiento de embeddings
# =========================

def store_embeddings(doc_id, text):
    """
    Divide el texto, genera embeddings y los almacena en Chroma.
    Retorna el número de chunks creados.
    """

    # 1. Chunking
    chunks, chunk_info = chunk_text(text)

    if not chunks:
        return 0

    # 2. Generación de embeddings
    # IMPORTANTE: esto es lo más costoso en PDFs grandes
    embeddings = model.encode(chunks).tolist()

    # 3. Construcción de metadatos
    metadatas = [
        {
            "doc_id": doc_id,
            "chunk_index": info["chunk_index"],
            "approx_page": info["approx_page"],
            "char_start": info["char_start"],
            "char_end": info["char_end"]
        }
        for info in chunk_info
    ]

    # 4. Almacenamiento en Chroma
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
    )

    return len(chunks)

# =========================
# Búsqueda semántica
# =========================

def search_similar(query, top_k=7, doc_id=None):
    """
    Busca chunks similares a la query.
    Puede filtrar por documento específico.
    """

    # Generar embedding de la query
    query_embedding = model.encode(query)

    # Chroma espera lista de listas
    if query_embedding.ndim == 1:
        query_embedding = [query_embedding.tolist()]
    elif query_embedding.ndim == 2:
        query_embedding = query_embedding.tolist()
    else:
        raise ValueError(
            f"Embedding con forma inesperada: {query_embedding.shape}"
        )

    # Filtro opcional por documento
    where_filter = {"doc_id": doc_id} if doc_id else None

    # Consulta a Chroma
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter
    )

    return results

# =========================
# Gestión de documentos
# =========================

def get_all_documents():
    """
    Retorna lista única de doc_id almacenados.
    """
    try:
        all_items = collection.get()

        if all_items and "metadatas" in all_items:
            doc_ids = {
                meta.get("doc_id")
                for meta in all_items["metadatas"]
                if meta and meta.get("doc_id")
            }
            return list(doc_ids)

        return []

    except Exception:
        return []


def delete_document(doc_id):
    """
    Elimina todos los chunks asociados a un documento.
    """
    try:
        all_items = collection.get(where={"doc_id": doc_id})

        if all_items and "ids" in all_items:
            collection.delete(ids=all_items["ids"])
            return True

        return False

    except Exception:
        return False
