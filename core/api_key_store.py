import os
from pathlib import Path

from core.app_paths import ENV_FILE_PATH
from core.file_utils import remove_env_key

try:
    import keyring
except ModuleNotFoundError:
    keyring = None


SERVICE_NAME = "novel-autowriter"
ACCOUNT_NAME = "google_api_key"


def has_secure_storage() -> bool:
    if keyring is None:
        return False
    try:
        backend = keyring.get_keyring()
    except Exception:
        return False
    backend_name = backend.__class__.__name__.lower()
    backend_module = backend.__class__.__module__.lower()
    return "fail" not in backend_name and ".fail" not in backend_module


def get_secure_api_key() -> str | None:
    if not has_secure_storage():
        return None
    try:
        value = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
    except Exception:
        return None
    if not value:
        return None
    stripped = value.strip()
    return stripped or None


def load_secure_api_key_into_environment() -> bool:
    secure_api_key = get_secure_api_key()
    if not secure_api_key:
        return False
    os.environ["GOOGLE_API_KEY"] = secure_api_key
    return True


def set_runtime_api_key(value: str) -> None:
    os.environ["GOOGLE_API_KEY"] = value.strip()


def save_api_key_to_secure_storage(value: str, env_path: Path = ENV_FILE_PATH) -> tuple[bool, str]:
    normalized_value = value.strip()
    if not normalized_value:
        return False, "API 키를 입력해 주세요."
    if not has_secure_storage():
        return False, "보안 저장소를 사용할 수 없습니다. `pip install -r requirements.txt` 후 다시 실행해 주세요."
    try:
        keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, normalized_value)
    except Exception as exc:
        return False, f"보안 저장소에 저장하지 못했습니다: {exc}"

    remove_env_key(env_path, "GOOGLE_API_KEY")
    os.environ["GOOGLE_API_KEY"] = normalized_value
    return True, "API 키를 보안 저장소에 저장했고 `.env`의 평문 키는 제거했습니다."


def delete_api_key_from_secure_storage() -> tuple[bool, str]:
    if not has_secure_storage():
        return False, "보안 저장소를 사용할 수 없습니다."
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except Exception as exc:
        return False, f"보안 저장소에서 삭제하지 못했습니다: {exc}"
    return True, "보안 저장소의 API 키를 삭제했습니다."


def env_file_has_key(path: Path = ENV_FILE_PATH, key: str = "GOOGLE_API_KEY") -> bool:
    if not path.exists():
        return False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    target_prefix = f"{key}="
    return any(line.startswith(target_prefix) for line in lines)
