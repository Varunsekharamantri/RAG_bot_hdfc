"""Single place for the Groq key, model choice, and a health check."""

import os
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


def model_candidates():
    preferred = (os.getenv("GROQ_MODEL") or "").strip()
    models = [preferred] if preferred else []
    models += [m for m in FALLBACK_MODELS if m not in models]
    return models


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
    """chat.completions.create with automatic fallback when a model is unavailable."""
    last_error = None
    for model in model_candidates():
        try:
            return _call(client, model, kwargs)
        except (NotFoundError, BadRequestError) as e:
            last_error = e  # model retired/unknown: try the next one
    raise last_error


def check_groq() -> Tuple[bool, str]:
    """Make a tiny call. Returns (ok, human-readable status)."""
    client = get_client()
    if client is None:
        return False, "No Groq key set. Add GROQ_API_KEY (or API_KEY) in Vercel environment variables."
    try:
        create_chat(client, messages=[{"role": "user", "content": "ping"}], max_tokens=64)
        return True, "Groq key accepted."
    except (AuthenticationError, PermissionDeniedError):
        return False, "Groq rejected the key (invalid, expired or revoked). Create a new key and update it in Vercel."
    except RateLimitError:
        return True, "Groq key accepted, but currently rate limited."
    except APIError as e:
        return False, f"Groq API error: {e}"
    except Exception as e:
        return False, f"Could not reach Groq: {e}"
