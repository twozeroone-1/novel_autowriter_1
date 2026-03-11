import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.app_paths import APP_ROOT


MODELS_CONFIG_PATH = APP_ROOT / "config" / "models.json"

DEFAULT_MODEL_CATALOG = {
    "models": [
        {"name": "gemini-1.5-pro"},
        {"name": "gemini-1.5-flash"},
        {"name": "gemini-2.0-pro-exp"},
        {"name": "gemini-2.0-flash", "pricing": {"input": 0.10, "output": 0.40}},
        {"name": "gemini-2.5-pro", "pricing": {"input": 1.25, "output": 10.00}},
        {"name": "gemini-2.5-flash", "pricing": {"input": 0.30, "output": 2.50}},
        {"name": "gemini-2.5-flash-lite", "pricing": {"input": 0.10, "output": 0.40}},
        {"name": "gemini-3-pro-preview", "pricing": {"input": 2.00, "output": 12.00}},
        {"name": "gemini-3-flash-preview", "pricing": {"input": 0.50, "output": 3.00}},
        {"name": "gemini-3.1-pro-preview", "pricing": {"input": 2.00, "output": 12.00}},
    ]
}


def _normalize_model_catalog(payload: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        return DEFAULT_MODEL_CATALOG

    models = payload.get("models")
    if not isinstance(models, list):
        return DEFAULT_MODEL_CATALOG

    normalized_models: list[dict[str, Any]] = []
    for entry in models:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        if not name:
            continue

        normalized_entry: dict[str, Any] = {"name": name}
        pricing = entry.get("pricing")
        if isinstance(pricing, dict):
            input_price = pricing.get("input")
            output_price = pricing.get("output")
            if isinstance(input_price, (int, float)) and isinstance(output_price, (int, float)):
                normalized_entry["pricing"] = {
                    "input": float(input_price),
                    "output": float(output_price),
                }
        normalized_models.append(normalized_entry)

    if not normalized_models:
        return DEFAULT_MODEL_CATALOG
    return {"models": normalized_models}


@lru_cache(maxsize=1)
def load_model_catalog(config_path: Path = MODELS_CONFIG_PATH) -> dict[str, list[dict[str, Any]]]:
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_MODEL_CATALOG
    return _normalize_model_catalog(payload)


def get_available_models() -> list[str]:
    return [entry["name"] for entry in load_model_catalog()["models"]]


def get_model_pricing(model_name: str) -> dict[str, float] | None:
    for entry in load_model_catalog()["models"]:
        if entry["name"] == model_name:
            pricing = entry.get("pricing")
            if isinstance(pricing, dict):
                return pricing
            return None
    return None
