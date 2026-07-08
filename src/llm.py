import requests
from typing import Optional

from src.config import OLLAMA_API_URL, OLLAMA_DEFAULT_MODEL


def query_ollama(prompt: str, model: Optional[str] = None,
                 temperature: float = 0.3, num_predict: int = 2000,
                 timeout: int = 120) -> str:
    model = model or OLLAMA_DEFAULT_MODEL
    try:
        resp = requests.post(
            f"{OLLAMA_API_URL}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": num_predict
                }
            },
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except requests.RequestException as e:
        raise RuntimeError(f"Ошибка Ollama: {e}")


def list_ollama_models() -> list:
    try:
        resp = requests.get(f"{OLLAMA_API_URL}/tags", timeout=10)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except requests.RequestException:
        return []
