"""Shared application state (thread-safe via lock)."""
import threading

_last_user_prompt: str = ""
_lock = threading.Lock()


def get_last_prompt() -> str:
    with _lock:
        return _last_user_prompt


def set_last_prompt(prompt: str):
    with _lock:
        global _last_user_prompt
        _last_user_prompt = prompt
