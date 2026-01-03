import os
import requests
import streamlit as st

# =========================
# Configuración de la página
# =========================

st.set_page_config(
    page_title="ChatPDF",
    page_icon="📄",
    layout="wide"
)

# =========================
# Configuración de la API
# =========================

# Detecta si está en Docker o en desarrollo local
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

UPLOAD_URL = f"{API_BASE}/upload_pdf"
ASK_URL = f"{API_BASE}/ask"
DOCS_URL = f"{API_BASE}/documents"

# =========================
# UI - Título principal
# =========================

st.title("📄 ChatPDF - Chat con tus PDFs")

# =========================
# Sidebar
# =========================

with st.sidebar:

    # ---------- Upload de PDFs ----------
    st.header("📄 Subir PDFs")

    uploaded_files = st.file_uploader(
        "Arrastra tus PDFs aquí",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.write(f"✅ {len(uploaded_files)} archivo(s) cargado(s)")

        if st.button("🚀 Procesar PDFs", type="primary"):
            with st.spinner("Procesando PDFs..."):
                for uploaded_file in uploaded_files:
                    try:
                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                "application/pdf",
                            )
                        }

                        response = requests.post(
                            UPLOAD_URL,
                            files=files,
                            timeout=60,
                        )

                        if response.status_code == 200:
                            st.success(f"✅ {uploaded_file.name}")
                        else:
                            st.error(f"❌ Error en {uploaded_file.name}")

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

                st.success("🎉 ¡Todos los PDFs procesados!")
                st.rerun()

    st.divider()

    # ---------- Documentos disponibles ----------
    st.header("📚 Documentos disponibles")

    try:
        response = requests.get(DOCS_URL, timeout=10)

        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])

            if documents:
                # Selector de documento
                selected_doc = st.selectbox(
                    "Buscar en:",
                    ["Todos los documentos"] + documents,
                    key="doc_selector",
                )

                # Guardar selección
                st.session_state.selected_doc_id = (
                    None if selected_doc == "Todos los documentos" else selected_doc
                )

                st.write(f"**Total: {len(documents)} documento(s)**")

                # Lista de documentos con opción de eliminar
                for doc in documents:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.text(f"📄 {doc}")

                    with col2:
                        if st.button("🗑️", key=f"delete_{doc}"):
                            try:
                                del_response = requests.delete(
                                    f"{DOCS_URL}/{doc}",
                                    timeout=10,
                                )

                                if del_response.status_code == 200:
                                    st.success(f"Eliminado: {doc}")
                                    st.rerun()
                                else:
                                    st.error("Error al eliminar")

                            except Exception as e:
                                st.error(f"Error: {str(e)}")

            else:
                st.info("No hay documentos cargados")
                st.session_state.selected_doc_id = None

        else:
            st.error("No se pudo obtener la lista de documentos")

    except Exception as e:
        st.error(f"Error al cargar documentos: {str(e)}")

    st.divider()

    # ---------- Información ----------
    st.markdown("### ℹ️ Instrucciones")
    st.markdown(
        """
        1. Sube uno o más PDFs
        2. Presiona "Procesar PDFs"
        3. Selecciona un documento específico o busca en todos
        4. Haz preguntas sobre el contenido
        """
    )

    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = []
        st.rerun()

# =========================
# Área principal de chat
# =========================

st.markdown("### 💬 Chat")

# Mostrar documento seleccionado
if st.session_state.get("selected_doc_id"):
    st.info(f"🔍 Buscando en: **{st.session_state.selected_doc_id}**")
else:
    st.info("🔍 Buscando en: **Todos los documentos**")

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================
# Input del usuario
# =========================

if prompt := st.chat_input("Pregunta algo sobre tus PDFs..."):

    # Guardar mensaje del usuario
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🤔 Pensando..."):
            try:
                payload = {"query": prompt}

                if st.session_state.get("selected_doc_id"):
                    payload["doc_id"] = st.session_state.selected_doc_id

                response = requests.post(
                    ASK_URL,
                    json=payload,
                    timeout=60,
                )

                if response.status_code == 200:
                    data = response.json()

                    answer = data.get("answer", "No recibí respuesta")
                    chunks_found = data.get("chunks_found", 0)
                    sources = data.get("sources", [])

                    st.markdown(answer)

                    # Mostrar fuentes
                    if sources:
                        st.markdown("---")
                        st.markdown("**📚 Fuentes consultadas:**")
                        for source in sources:
                            st.markdown(
                                f"- 📄 **{source['document']}** "
                                f"(Página ~{source['page']}, Fragmento {source['fragment']})"
                            )

                    elif chunks_found > 0:
                        st.caption(
                            f"ℹ️ Encontrados {chunks_found} fragmentos relevantes"
                        )

                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )

                else:
                    error_msg = f"❌ Error {response.status_code}: {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

            except requests.exceptions.Timeout:
                error_msg = "⏱️ La solicitud tardó demasiado. Intenta de nuevo."
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

# =========================
# Footer
# =========================

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
        deepPDF Chat
    </div>
    """,
    unsafe_allow_html=True,
)
