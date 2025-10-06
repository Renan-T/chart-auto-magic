# backend/ai_client.py
from __future__ import annotations
import os, httpx, json
from typing import Any, Dict, List, Optional

# Carrega .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

def _get_env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default if default is not None else "")
    return v.strip() if isinstance(v, str) else v

OPENROUTER_API_KEY = _get_env("OPENROUTER_API_KEY")
BASE_URL = _get_env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
DEFAULT_MODEL = _get_env("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
SITE_URL = _get_env("OPENROUTER_SITE_URL")
APP_NAME = _get_env("OPENROUTER_APP_NAME", "AutoDash BI Comercial")

def _headers() -> Dict[str, str]:
    if not OPENROUTER_API_KEY:
        # Falha cedo e claramente (em vez de mandar "Bearer ")
        raise RuntimeError("OPENROUTER_API_KEY ausente. Configure backend/.env ou a variável de ambiente.")
    h = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if SITE_URL:
        h["HTTP-Referer"] = SITE_URL
    if APP_NAME:
        h["X-Title"] = APP_NAME
    return h

async def chat_json(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> Dict[str, Any]:
    use_model = (model or DEFAULT_MODEL).strip()
    if not use_model:
        raise RuntimeError("Nenhum modelo configurado. Defina OPENROUTER_MODEL ou passe `model` na requisição.")

    payload = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BASE_URL}/chat/completions", headers=_headers(), json=payload)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            # Remove fences tipo ```json
            content = content.strip("`")
            if content.lower().startswith("json"):
                content = content[4:].strip()
        try:
            return json.loads(content)
        except Exception:
            return {"_raw": content}
