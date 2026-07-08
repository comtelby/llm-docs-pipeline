from fastapi import APIRouter, Form, HTTPException
from src.llm import query_ollama, list_ollama_models
from src.state import set_last_prompt

router = APIRouter()


@router.get("/models")
async def list_models():
    models = list_ollama_models()
    if not models:
        raise HTTPException(503, "Ollama недоступна")
    return {"models": models}


@router.post("/chat")
async def chat(prompt: str = Form(...), model: str = Form(default="qwen2.5-coder:7b")):
    set_last_prompt(prompt.strip())
    try:
        response = query_ollama(prompt, model=model, timeout=120)
        return {"response": response, "prompt_saved": True}
    except RuntimeError as e:
        raise HTTPException(500, f"Ошибка Ollama: {e}")
