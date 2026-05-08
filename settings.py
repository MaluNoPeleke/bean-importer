"""Read/write the local .env so the UI can manage provider config without a restart."""
import os
import shutil
from pathlib import Path

from dotenv import dotenv_values, set_key

ENV_PATH = Path(__file__).parent / ".env"
ENV_EXAMPLE = Path(__file__).parent / ".env.example"

PROVIDERS = {
    "anthropic": {
        "label": "Anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "key_url": "https://console.anthropic.com/settings/keys",
        "models": [
            "anthropic/claude-opus-4-7",
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-haiku-4-5-20251001",
        ],
        "default_model": "anthropic/claude-sonnet-4-6",
    },
    "gemini": {
        "label": "Google Gemini",
        "key_env": "GEMINI_API_KEY",
        "key_url": "https://aistudio.google.com/app/apikey",
        "models": [
            "gemini/gemini-2.5-pro",
            "gemini/gemini-2.5-flash",
        ],
        "default_model": "gemini/gemini-2.5-pro",
    },
    "openai": {
        "label": "OpenAI",
        "key_env": "OPENAI_API_KEY",
        "key_url": "https://platform.openai.com/api-keys",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
        ],
        "default_model": "gpt-4o",
    },
}


def _ensure_env_file() -> None:
    if not ENV_PATH.exists():
        if ENV_EXAMPLE.exists():
            shutil.copy(ENV_EXAMPLE, ENV_PATH)
        else:
            ENV_PATH.write_text("", encoding="utf-8")


def _provider_for_model(model: str) -> str | None:
    m = (model or "").lower()
    if m.startswith("anthropic/"):
        return "anthropic"
    if m.startswith("gemini/"):
        return "gemini"
    if m.startswith("openai/") or m.startswith("gpt-"):
        return "openai"
    return None


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 4:
        return "•" * len(key)
    return "••••" + key[-4:]


def read_settings() -> dict:
    """Return current provider/model + whether a key is set (never the key itself)."""
    values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    model = os.environ.get("LLM_MODEL") or values.get("LLM_MODEL") or ""
    provider = _provider_for_model(model)

    has_key = False
    key_masked = ""
    if provider:
        env_name = PROVIDERS[provider]["key_env"]
        key = os.environ.get(env_name) or values.get(env_name) or ""
        # Treat the placeholder from .env.example as "no real key".
        if key and "YOUR_KEY_HERE" not in key:
            has_key = True
            key_masked = _mask(key)

    return {
        "provider": provider,
        "model": model,
        "has_key": has_key,
        "key_masked": key_masked,
        "providers": {
            slug: {
                "label": p["label"],
                "key_url": p["key_url"],
                "models": p["models"],
                "default_model": p["default_model"],
            }
            for slug, p in PROVIDERS.items()
        },
    }


def write_settings(provider: str, model: str, api_key: str | None) -> None:
    """Persist to .env and update os.environ so the running process sees the change."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unbekannter Provider: {provider}")
    if model not in PROVIDERS[provider]["models"]:
        raise ValueError(f"Modell '{model}' gehört nicht zu Provider '{provider}'")

    _ensure_env_file()
    key_env = PROVIDERS[provider]["key_env"]

    set_key(str(ENV_PATH), "LLM_MODEL", model, quote_mode="never")
    os.environ["LLM_MODEL"] = model

    if api_key:
        set_key(str(ENV_PATH), key_env, api_key, quote_mode="never")
        os.environ[key_env] = api_key
