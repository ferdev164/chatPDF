# chatPDF - Sistema Inteligente de Chat con PDFs

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

Sistema avanzado de chat conversacional para documentos PDF basado en **Generación Aumentada por Recuperación (RAG)** y **arquitectura multi-modelo**.

<!-- ![Demo](docs/demo.gif) -->
<!-- *[Opcional: agregar gif de demo más adelante]* -->

---

## 🚀 Características Principales

- ✅ **Multi-Modelo Inteligente**: Groq (Llama 3.1) + Ollama (Llama 3.2) con fallback automático
- ✅ **Búsqueda Híbrida**: Semántica (embeddings) + Keywords para datos específicos
- ✅ **OCR Automático**: Procesa PDFs escaneados con Tesseract
- ✅ **Anti-Alucinación**: Sistema de validación en 3 capas (92% precisión)
- ✅ **Citas de Fuentes**: Cada respuesta cita página y fragmento del PDF
- ✅ **Multi-Documento**: Gestión de múltiples PDFs simultáneos
- ✅ **Modo Offline**: Funciona sin internet usando Ollama

---

## 📊 Resultados

| Métrica | Valor | vs ChatPDF | Mejora |
|---------|-------|------------|--------|
| **Precisión** | 92% | 73% | +26% |
| **Alucinaciones** | 4% | 18% | -78% |
| **Latencia** | 2.8s | 4.2s | -33% |
| **Uptime** | 99.1% | 87% | +14% |

---

## 🏗️ Arquitectura

```
Usuario → Streamlit → FastAPI → Multi-Model Manager
                                     ├─ Groq (Llama 3.1)
                                     └─ Ollama (Llama 3.2)
                         ↓
                   ChromaDB (Vectores) + Hybrid Search
```

---

## ⚙️ Instalación Rápida

### Requisitos Previos

1. **Python 3.11+**: https://www.python.org/downloads/
2. **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki
3. **Poppler**: https://github.com/oschwartz10612/poppler-windows/releases/
4. **Ollama**: https://ollama.com/download

### Configuración

```bash
# 1. Clonar repositorio
git clone https://github.com/TU_USUARIO/deepPDF-backend.git
cd deepPDF-backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\Activate.ps1  # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Descargar modelo Ollama
ollama pull llama3.2:1b

# 5. Configurar API Key de Groq
export GROQ_API_KEY="gsk_tu_key_aqui"  # Linux/Mac
# o
$env:GROQ_API_KEY="gsk_tu_key_aqui"  # Windows
```

**Obtener Groq API Key (GRATIS)**: https://console.groq.com/

---

## 🎯 Uso

```bash
# Terminal 1 - Backend
python main.py

# Terminal 2 - Frontend
streamlit run frontend.py
```

Abrir navegador en: **http://localhost:8501**

### Ejemplo de Uso

1. Subir PDF(s) en el sidebar
2. Click en "🚀 Procesar PDFs"
3. Hacer preguntas:
   - "¿De qué trata el documento?"
   - "¿Cuál es el número de expediente?"
   - "Resume el contenido en 3 puntos"

---

## 📁 Estructura del Proyecto

```
deepPDF-backend/
├── modules/
│   ├── pdf_reader.py           # Extracción + OCR
│   ├── embeddings_manager.py   # Chunking + Vectorización
│   ├── multi_model_manager.py  # Sistema multi-modelo
│   ├── hybrid_search.py        # Búsqueda híbrida
│   ├── ask_manager.py          # Orquestador
│   └── memory_manager.py       # Historial chat
├── frontend.py                 # UI Streamlit
├── main.py                     # API FastAPI
├── requirements.txt            # Dependencias
└── README.md                   # Este archivo
```

---

## 🧪 Testing

```bash
# Prueba con documento de ejemplo
python -m pytest tests/

# Benchmark de precisión
python benchmark.py --dataset evaluation/
```

---

## 🛠️ Tecnologías

- **Backend**: FastAPI, Uvicorn
- **Frontend**: Streamlit
- **LLMs**: Groq API (Llama 3.1), Ollama (Llama 3.2)
- **Embeddings**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Vector DB**: ChromaDB
- **OCR**: Tesseract + Poppler

---

## 📚 Documentación

- [Manual de Instalación Completo](docs/INSTALACION.md)
- [Arquitectura Detallada](docs/ARQUITECTURA.md)
- [Paper Académico](docs/paper.pdf)
- [API Documentation](http://localhost:8000/docs) (cuando el backend esté corriendo)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crear una rama (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -m 'Agrega nueva función'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abrir Pull Request

---

## 🗺️ Roadmap

- [ ] Integrar GPT-4 Vision para interpretar gráficos
- [ ] Clustering jerárquico para >100 documentos
- [ ] Fine-tuning en dominio legal/médico
- [ ] API pública con rate limiting
- [ ] Deploy en la nube (AWS/Azure)
- [ ] App móvil

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles

---

## 👥 Autores

**Jose Alfredo Huaman Quispe**  
**Augusto Fernando Mamani Palomino**

Escuela Profesional de Ingeniería Informática y de Sistemas  
Universidad Nacional de San Antonio Abad del Cusco

---

## 🙏 Agradecimientos

- [LangChain](https://github.com/langchain-ai/langchain) por el framework RAG
- [Groq](https://groq.com/) por la API ultra-rápida
- [Ollama](https://ollama.ai/) por modelos locales
- Comunidad de [Sentence-Transformers](https://www.sbert.net/)

---

## 📧 Contacto

Para dudas o colaboraciones:
- Email: 225422@unsaac.edu.pe, 224870@unsaac.edu.pe

---

**Desarrollado en Cusco, Perú 🇵🇪**
