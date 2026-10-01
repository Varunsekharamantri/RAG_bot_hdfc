"""Single place for the Groq key, model choice, and a health check."""

import os
import time
from typing import Optional, Tuple

from groq import (
    Groq, AuthenticationError, PermissionDeniedError, RateLimitError,
    APIError, NotFoundError, BadRequestError,
)

KEY_ENV_NAMES = ("GROQ_API_KEY", "API_KEY")

# Preferred model first (override with GROQ_MODEL); the rest are used only if Groq
# retires or rejects the model. Groq retired llama-3.1-8b-instant and
# llama-3.3-70b-versatile on 2026-08-16; see console.groq.com/docs/deprecations.
FALLBACK_MODELS = ("openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.6-27b")


def get_api_key() -> Optional[str]:
    for name in KEY_ENV_NAMES:
        value = (os.getenv(name) or "").strip().strip('"').strip("'")
        if value:
            return value
    return None


def get_client() -> Optional[Groq]:
    key = get_api_key()
    return Groq(api_key=key) if key else None


# Models that are not chat/text generators; never auto-select these.
_NOT_CHAT = ("whisper", "tts", "orpheus", "guard", "safeguard", "embed", "playai", "compound")
_CACHE_SECONDS = 3600
_available = {"at": 0.0, "ids": None}
last_used = {"model": None}


def available_models(client, force=False):
    """Model ids Groq currently serves (cached ~1h). None if the list can't be fetched."""
    now = time.time()
    if not force and _available["ids"] is not None and now - _available["at"] < _CACHE_SECONDS:
        return _available["ids"]
    try:
        ids = [m.id for m in client.models.list().data]
    except Exception:
        return _available["ids"]  # stale list (or None) is better than failing
    _available.update(at=now, ids=ids)
    return ids


def preferred_models():
    preferred = (os.getenv("GROQ_MODEL") or "").strip()
    models = [preferred] if preferred else []
    return models + [m for m in FALLBACK_MODELS if m not in models]


def model_candidates(client=None):
    """Preferred models that are live, then any other live chat model, best guess first."""
    wanted = preferred_models()
    live = available_models(client) if client else None
    if not live:
        return wanted  # can't discover: fall back to the static list
    chosen = [m for m in wanted if m in live]
    others = sorted(m for m in live if m not in chosen and not any(t in m.lower() for t in _NOT_CHAT))
    others.sort(key=lambda m: 0 if "gpt-oss" in m else 1 if "llama" in m else 2 if "qwen" in m else 3)
    return chosen + others


def _call(client, model, kwargs):
    # gpt-oss are reasoning models: keep reasoning short so it doesn't eat the token budget.
    if model.startswith("openai/gpt-oss"):
        try:
            return client.chat.completions.create(model=model, reasoning_effort="low", **kwargs)
        except BadRequestError as e:
            if "reasoning" not in str(e).lower():
                raise
    return client.chat.completions.create(model=model, **kwargs)


def create_chat(client, **kwargs):
    """chat.completions.create that keeps trying live models if one is retired or rejected."""
    last_error = None
    for model in model_candidates(client)[:6]:
        try:
            response = _call(client, model, kwargs)
            last_used["model"] = model
            return response
        except (NotFoundError, BadRequestError) as e:
            last_error = e
            _available["at"] = 0.0  # re-discover live models next time
    if last_error is None:
        raise RuntimeError("No usable Groq chat model is available.")
    raise last_error


def check_groq() -> Tuple[str, str]:
    """Tiny live call. Returns (status, detail); status is 'ok', 'degraded' or 'error'."""
    client = get_client()
    if client is None:
        return "error", "No Groq key set. Add GROQ_API_KEY (or API_KEY) in Vercel environment variables."
    try:
        create_chat(client, messages=[{"role": "user", "content": "ping"}], max_tokens=64)
    except (AuthenticationError, PermissionDeniedError):
        return "error", "Groq rejected the key (invalid, expired or revoked). Create a new key and update it in Vercel."
    except RateLimitError:
        return "ok", "Groq key accepted, but currently rate limited."
    except APIError as e:
        return "error", f"Groq API error: {e}"
    except Exception as e:
        return "error", f"Could not reach Groq: {e}"
    used = last_used["model"]
    want = preferred_models()[0]
    if used != want:
        return "degraded", f"Working, but preferred model '{want}' is unavailable; using '{used}'. Update GROQ_MODEL / FALLBACK_MODELS."
    return "ok", f"Groq key accepted; using '{used}'."
