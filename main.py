# =========================
# Configuración global
# =========================

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from transformers.utils import logging
logging.set_verbosity_error()

import os
import uuid

from fastapi import FastAPI, UploadFile, File

# =========================
# Imports internos del proyecto
# =========================

from modules.pdf_reader import extract_text_from_pdf
from modules.embeddings_manager import (
    store_embeddings,
    search_similar,
    get_all_documents,
    delete_document,
)
from modules.ask_manager import ask_gemini
from modules.memory_manager import add_to_memory, get_memory
from modules.hybrid_search import smart_search  # NUEVO

# =========================
# Inicialización de la app
# =========================

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================
# Endpoints
# =========================

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Sube un PDF, extrae su texto, genera embeddings y elimina el archivo físico.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Guardar archivo temporalmente
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extraer texto del PDF
    text = extract_text_from_pdf(file_path)

    # Eliminar archivo tras procesarlo
    os.remove(file_path)

    # Generar embeddings y almacenar en la base vectorial
    num_chunks = store_embeddings(file.filename, text)

    # Preview del contenido
    preview = text[:500]

    return {
        "filename": file.filename,
        "text_preview": preview,
        "characters_extracted": len(text),
        "chunks_created": num_chunks,
    }


@app.get("/search")
def search(query: str, doc_id: str = None):
    """
    Endpoint simple de búsqueda vectorial (debug / testing).
    """
    results = search_similar(query, doc_id=doc_id)
    return results


@app.get("/documents")
def list_documents():
    """
    Listar todos los documentos almacenados en la base vectorial.
    """
    docs = get_all_documents()
    return {
        "documents": docs,
        "count": len(docs),
    }


@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    """
    Eliminar un documento específico junto con sus embeddings.
    """
    success = delete_document(doc_id)
    if success:
        return {"message": f"Documento '{doc_id}' eliminado exitosamente"}
    return {"error": f"No se pudo eliminar '{doc_id}'"}


@app.post("/ask")
async def ask(request: dict):
    """
    Endpoint principal de preguntas:
    - Busca contexto relevante en PDFs
    - Construye prompt con fragmentos + memoria
    - Llama al modelo LLM
    """

    question = request.get("query")
    doc_id = request.get("doc_id")

    if not question:
        return {"error": "Falta el campo 'query'."}

    # Manejo de sesión de conversación
    session_id = request.get("session_id", str(uuid.uuid4()))
    add_to_memory(session_id, "user", question)

    # =========================
    # Búsqueda híbrida de contexto
    # =========================

    search_results = smart_search(question, doc_id=doc_id)

    # Resultados devueltos por Chroma
    chunks = search_results.get("documents", [[]])[0]
    metadatas = search_results.get("metadatas", [[]])[0]

    # =========================
    # Construcción del contexto
    # =========================

    if chunks:
        context_parts = []
        sources = []

        for idx, (chunk, meta) in enumerate(zip(chunks, metadatas)):
            doc_name = meta.get("doc_id", "desconocido")
            page = meta.get("approx_page", "?")
            chunk_num = meta.get("chunk_index", idx)

            context_parts.append(
                f"[FRAGMENTO {idx+1} - {doc_name} - Página ~{page}]\n{chunk}"
            )

            sources.append({
                "fragment": idx + 1,
                "document": doc_name,
                "page": page,
                "chunk_index": chunk_num,
            })

        context = "\n\n".join(context_parts)

        doc_info = (
            f" del documento '{doc_id}'"
            if doc_id
            else " de los documentos disponibles"
        )

        # =========================
        # DEBUG: mostrar fragmentos enviados a la IA
        # =========================
        print("\n" + "=" * 80)
        print("FRAGMENTOS ENVIADOS A LA IA:")
        for idx, part in enumerate(context_parts[:5]):  # Mostrar primeros 5
            print(f"\n--- Fragmento {idx+1} ---")
            print(part[:200] + "..." if len(part) > 200 else part)
        print("=" * 80 + "\n")

        # =========================
        # Prompt final
        # =========================
        prompt = f"""Eres un asistente que responde preguntas basándose ÚNICAMENTE en el siguiente contenido{doc_info}.

CONTENIDO DEL PDF:
{context}

HISTORIAL DE LA CONVERSACIÓN:
{get_memory(session_id)}

PREGUNTA DEL USUARIO:
{question}

INSTRUCCIONES CRÍTICAS:
1. Lee TODOS los fragmentos cuidadosamente antes de responder
2. Si la respuesta está en algún fragmento, cítalo específicamente: "Según el Fragmento X..."
3. Si buscas un número, fecha o dato específico, revisa TODOS los fragmentos
4. Si te hacen una pregunta que no se relaciona con el contenido, respondela vagamente basándote en tu conocimiento general
5. NO inventes información que no esté en los fragmentos
6. Si un fragmento menciona algo parcialmente relacionado, menciónalo
7. Si NO encuentras la información en NINGÚN fragmento, responde usando conocimiento general

RESPUESTA:"""

    else:
        # Caso sin PDFs o sin resultados relevantes
        prompt = f"""El usuario pregunta: "{question}"

Pero NO hay documentos PDF cargados en el sistema todavía, o no hay información relevante{' en el documento seleccionado' if doc_id else ''}.

Responde de manera amigable explicando que:
1. Necesita subir documentos PDF primero
2. Una vez subidos, podrás responder preguntas sobre su contenido
3. Mantén un tono útil y guía al usuario
4. Responde vagamente con conocimiento general

RESPUESTA:"""

        sources = []

    # =========================
    # Llamada al modelo
    # =========================

    answer = ask_gemini(prompt)
    add_to_memory(session_id, "assistant", answer)

    return {
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "chunks_found": len(chunks),
        "sources": sources,
        "searched_in": doc_id if doc_id else "all documents",
    }
