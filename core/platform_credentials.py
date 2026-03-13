import json

try:
    import keyring
except ModuleNotFoundError:
    keyring = None


SERVICE_NAME = "novel-autowriter-publishing"


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


def save_platform_credentials(
    project_name: str,
    platform_name: str,
    username: str,
    password: str,
) -> tuple[bool, str]:
    normalized_username = username.strip()
    normalized_password = password.strip()
    if not normalized_username or not normalized_password:
        return False, "아이디와 비밀번호를 모두 입력해 주세요."
    if not has_secure_storage():
        return False, "보안 저장소를 사용할 수 없습니다."

    payload = json.dumps(
        {
            "username": normalized_username,
            "password": normalized_password,
        },
        ensure_ascii=False,
    )
    try:
        keyring.set_password(SERVICE_NAME, _account_name(project_name, platform_name), payload)
    except Exception as exc:
        return False, f"보안 저장소에 저장하지 못했습니다. {exc}"
    return True, "플랫폼 계정을 보안 저장소에 저장했습니다."


def load_platform_credentials(project_name: str, platform_name: str) -> dict[str, str]:
    if not has_secure_storage():
        return {"username": "", "password": ""}
    try:
        raw_payload = keyring.get_password(SERVICE_NAME, _account_name(project_name, platform_name))
    except Exception:
        return {"username": "", "password": ""}
    if not raw_payload:
        return {"username": "", "password": ""}

    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {"username": "", "password": ""}

    return {
        "username": str(payload.get("username", "")),
        "password": str(payload.get("password", "")),
    }


def clear_platform_credentials(project_name: str, platform_name: str) -> tuple[bool, str]:
    if not has_secure_storage():
        return False, "보안 저장소를 사용할 수 없습니다."
    try:
        keyring.delete_password(SERVICE_NAME, _account_name(project_name, platform_name))
    except Exception as exc:
        return False, f"보안 저장소에서 삭제하지 못했습니다. {exc}"
    return True, "플랫폼 계정을 보안 저장소에서 삭제했습니다."


def _account_name(project_name: str, platform_name: str) -> str:
    return f"{project_name.strip()}:{platform_name.strip()}:credentials"
