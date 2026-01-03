# Crear archivo con instrucciones de setup
cat > SETUP_WINDOWS.md << 'EOF'
# Setup en Windows

## 1. Instalar Python 3.12
- Descargar de: https://www.python.org/downloads/
- ✅ MARCAR: "Add Python to PATH"

## 2. Instalar Tesseract OCR
- Descargar: https://github.com/UB-Mannheim/tesseract/wiki
- Instalar en: C:\Program Files\Tesseract-OCR

## 3. Instalar Poppler
- Descargar: https://github.com/oschwartz10612/poppler-windows/releases/
- Extraer en: C:\poppler

## 4. Instalar Ollama
- Descargar: https://ollama.com/download/windows
- Instalar y ejecutar: ollama pull llama3.2:1b

## 5. Configurar API Keys
- Buscar "variables de entorno" en Windows
- Agregar:
  * GROQ_API_KEY = tu_key
  * GEMINI_API_KEY = tu_key

## 6. Ejecutar
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
# En otra terminal:
streamlit run frontend.py
```
EOF