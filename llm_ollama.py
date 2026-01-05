from typing import Optional
import requests

TIMEOUT_SECONDS: int = 120


def ollama_chat(base_url: str, model: str, system: str, user: str) -> str:
    
    url = base_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    r = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]
