import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class MultiModelManager:
    """
    Gestor inteligente de múltiples modelos de IA con fallback automático.
    Proveedores soportados:
    - Groq (API remota)
    - Ollama (local)
    """

    def __init__(self):
        # =========================
        # Configuración de modelos
        # =========================
        self.models = {
            "groq": {
                "enabled": bool(os.getenv("GROQ_API_KEY")),
                "key": os.getenv("GROQ_API_KEY"),
                "url": "https://api.groq.com/openai/v1/chat/completions",
                "model": "llama-3.3-70b-versatile",
                "priority": 1,
                "timeout": 15,
                "description": "Groq (ultra rápido)",
            },
            "ollama": {
                "enabled": self._check_ollama_available(),
                "url": "http://localhost:11434/api/generate",
                "model": "llama3.2:1b",
                "priority": 2,
                "timeout": 30,
                "description": "Ollama local (sin límites)",
            },
        }

        # =========================
        # Estadísticas de uso
        # =========================
        self.stats = {
            "groq": {"calls": 0, "errors": 0, "total_time": 0},
            "ollama": {"calls": 0, "errors": 0, "total_time": 0},
        }

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------

    def _check_ollama_available(self) -> bool:
        """Verifica si Ollama está corriendo localmente"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def ask(self, prompt: str, preferred_model: Optional[str] = None) -> Dict[str, Any]:
        """
        Realiza una consulta a los modelos disponibles.
        Si preferred_model falla, usa fallback automático.
        """
        all_errors = []

        # 1. Intentar modelo preferido si se especifica
        if preferred_model and preferred_model in self.models:
            result = self._try_model(preferred_model, prompt)
            if result["success"]:
                return result
            all_errors.append({preferred_model: result.get("error")})

        # 2. Intentar modelos habilitados por prioridad
        sorted_models = sorted(
            [
                (name, cfg)
                for name, cfg in self.models.items()
                if cfg["enabled"]
            ],
            key=lambda x: x[1]["priority"],
        )

        for model_name, _ in sorted_models:
            result = self._try_model(model_name, prompt)
            if result["success"]:
                return result
            all_errors.append({model_name: result.get("error")})

        # 3. Si todos fallan
        return {
            "success": False,
            "answer": "❌ Error: Todos los modelos fallaron. Verifica tu conexión y configuración.",
            "errors": all_errors,
        }

    # ------------------------------------------------------------------
    # Ejecución por modelo
    # ------------------------------------------------------------------

    def _try_model(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Intenta ejecutar un modelo específico"""
        config = self.models[model_name]

        if not config["enabled"]:
            return {"success": False, "error": f"{model_name} no está habilitado"}

        self.stats[model_name]["calls"] += 1
        start_time = datetime.now()

        try:
            print(f"🤖 Intentando con {config['description']}...")

            if model_name == "groq":
                result = self._call_groq(config, prompt)
            elif model_name == "ollama":
                result = self._call_ollama(config, prompt)
            else:
                raise ValueError("Modelo desconocido")

            elapsed = (datetime.now() - start_time).total_seconds()
            self.stats[model_name]["total_time"] += elapsed

            if result["success"]:
                result["time"] = elapsed
                result["model"] = model_name
                print(f"✅ Respuesta de {config['description']} en {elapsed:.2f}s")
            else:
                self.stats[model_name]["errors"] += 1
                print(f"❌ Error en {model_name}: {result.get('error')}")

            return result

        except Exception as e:
            self.stats[model_name]["errors"] += 1
            print(f"❌ Excepción en {model_name}: {str(e)}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Implementaciones por proveedor
    # ------------------------------------------------------------------

    def _call_groq(self, config: Dict, prompt: str) -> Dict[str, Any]:
        """Llama a la API de Groq"""
        response = requests.post(
            config["url"],
            headers={
                "Authorization": f"Bearer {config['key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000,
                "top_p": 0.9,
            },
            timeout=config["timeout"],
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "answer": data["choices"][0]["message"]["content"],
            }

        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.text}",
        }

    def _call_ollama(self, config: Dict, prompt: str) -> Dict[str, Any]:
        """Llama a Ollama local"""
        response = requests.post(
            config["url"],
            json={
                "model": config["model"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 1000,
                },
            },
            timeout=config["timeout"],
        )

        if response.status_code == 200:
            data = response.json()
            return {"success": True, "answer": data["response"]}

        return {"success": False, "error": f"HTTP {response.status_code}"}

    # ------------------------------------------------------------------
    # Información y métricas
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Retorna estadísticas de uso por modelo"""
        return {
            model: {
                "calls": stats["calls"],
                "errors": stats["errors"],
                "avg_time": (
                    stats["total_time"] / stats["calls"]
                    if stats["calls"] > 0
                    else 0
                ),
                "success_rate": (
                    (stats["calls"] - stats["errors"]) / stats["calls"] * 100
                    if stats["calls"] > 0
                    else 0
                ),
            }
            for model, stats in self.stats.items()
        }

    def get_available_models(self) -> list:
        """Retorna lista de modelos disponibles"""
        return [
            {
                "name": name,
                "description": config["description"],
                "enabled": config["enabled"],
                "priority": config["priority"],
            }
            for name, config in self.models.items()
        ]


# Instancia global (singleton)
model_manager = MultiModelManager()
