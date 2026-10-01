"""Single place for reading the Groq key and checking that Groq accepts it."""

import os
from typing import Optional, Tuple

from groq import Groq, AuthenticationError, PermissionDeniedError, RateLimitError, APIError, NotFoundError, BadRequestError

KEY_ENV_NAMES = ("GROQ_API_KEY", "API_KEY")
# Preferred model first (override with GROQ_MODEL); the rest are used only if Groq
# retires or rejects the model, so a deprecation doesn't take the site down.
FALLBACK_MODELS = ("llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it")


def model_candidates():
    preferred = (os.getenv("GROQ_MODEL") or "").strip()
    models = [preferred] if preferred else []
    models += [m for m in FALLBACK_MODELS if m not in models]
    return models


def create_chat(client, **kwargs):
    """chat.completions.create with automatic fallback when a model is unavailable."""
    last_error = None
    for model in model_candidates():
        try:
            return client.chat.completions.create(model=model, **kwargs)
        except (NotFoundError, BadRequestError) as e:
            last_error = e  # model retired/unknown: try the next one
    raise last_error


def get_api_key() -> Optional[str]:
    for name in KEY_ENV_NAMES:
        value = (os.getenv(name) or "").strip().strip('"').strip("'")
        if value:
            return value
    return None


def get_client() -> Optional[Groq]:
    key = get_api_key()
    return Groq(api_key=key) if key else None


def check_groq() -> Tuple[bool, str]:
    """Make a 1-token call. Returns (ok, human-readable status)."""
    client = get_client()
    if client is None:
        return False, "No Groq key set. Add GROQ_API_KEY (or API_KEY) in Vercel environment variables."
    try:
        create_chat(
            client,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        return True, "Groq key accepted."
    except (AuthenticationError, PermissionDeniedError):
        return False, "Groq rejected the key (invalid, expired or revoked). Create a new key and update it in Vercel."
    except RateLimitError:
        return True, "Groq key accepted, but currently rate limited."
    except APIError as e:
        return False, f"Groq API error: {e}"
    except Exception as e:
        return False, f"Could not reach Groq: {e}"
