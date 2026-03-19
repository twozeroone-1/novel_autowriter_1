import os


LOCAL_RUNTIME = "local"
CLOUD_RUNTIME = "community_cloud"
STREAMLIT_SECRET_KEYS = (
    "APP_RUNTIME",
    "GOOGLE_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_BACKEND",
    "GITHUB_STORAGE_REPO",
    "GITHUB_STORAGE_TOKEN",
)


def get_runtime_mode() -> str:
    value = str(os.getenv("APP_RUNTIME", LOCAL_RUNTIME)).strip().lower()
    if value == CLOUD_RUNTIME:
        return CLOUD_RUNTIME
    return LOCAL_RUNTIME


def is_cloud_runtime() -> bool:
    return get_runtime_mode() == CLOUD_RUNTIME


def get_cloud_storage_repo() -> str:
    return str(os.getenv("GITHUB_STORAGE_REPO", "")).strip()


def get_cloud_storage_token() -> str:
    return str(os.getenv("GITHUB_STORAGE_TOKEN", "")).strip()


def validate_cloud_storage_settings() -> None:
    if not is_cloud_runtime():
        return

    missing: list[str] = []
    if not get_cloud_storage_repo():
        missing.append("GITHUB_STORAGE_REPO")
    if not get_cloud_storage_token():
        missing.append("GITHUB_STORAGE_TOKEN")

    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Community Cloud storage settings are missing: {joined}")


def load_streamlit_secrets_into_environment(keys: tuple[str, ...] = STREAMLIT_SECRET_KEYS) -> bool:
    try:
        import streamlit as st
    except Exception:
        return False

    loaded_any = False
    for key in keys:
        if str(os.getenv(key, "")).strip():
            continue
        try:
            value = st.secrets.get(key, "")
        except Exception:
            value = ""
        text = str(value).strip()
        if not text:
            continue
        os.environ[key] = text
        loaded_any = True
    return loaded_any
