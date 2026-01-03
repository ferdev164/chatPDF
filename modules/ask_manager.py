import os 
from modules.multi_model_manager import model_manager

def ask_gemini(prompt: str) -> str:
    """
    Función de compatibilidad - ahora usa Groq/Ollama
    (mantenemos el nombre para no romper código existente)
    """
    try:
        result = model_manager.ask(prompt)
        return result['answer']
    except Exception as e:
        # Imprime el error real en consola para depuración
        print(f"[ask_gemini ERROR] Falló al generar respuesta: {e}")
        return "❌ Error: Todos los modelos fallaron. Verifica tu conexión y configuración."

def ask_with_info(prompt: str, preferred_model: str = None) -> dict:
    """
    Versión extendida que retorna más información
    """
    try:
        return model_manager.ask(prompt, preferred_model)
    except Exception as e:
        print(f"[ask_with_info ERROR] Falló al generar respuesta: {e}")
        return {"answer": "❌ Error: Todos los modelos fallaron. Verifica tu conexión y configuración."}
