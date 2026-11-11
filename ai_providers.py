# ai_providers.py
import base64
import hashlib
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests

PROVIDERS = {
    "NVIDIA": {
        "name": "NVIDIA",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "models_endpoint": "/models",
        "config_key": "nvidia",
        "header_key": "Authorization",
        "header_prefix": "Bearer ",
        "get_models_url": lambda base: f"{base}/models",
    },
    "Gemini": {
        "name": "Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models_endpoint": "/models",
        "config_key": "gemini",
        "header_key": "x-goog-api-key",
        "header_prefix": "",
        "get_models_url": lambda base: f"{base}/models",
    },
    "OpenRouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models_endpoint": "/models",
        "config_key": "openrouter",
        "header_key": "Authorization",
        "header_prefix": "Bearer ",
        "get_models_url": lambda base: f"{base}/models",
    },
}

ENCRYPTION_SALT = b"qiranas_ai_key_salt_v1"

def _derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=ENCRYPTION_SALT,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_key(plain_key: str, machine_id: str = "default") -> str:
    if not plain_key:
        return ""
    key = _derive_key(machine_id)
    f = Fernet(key)
    return f.encrypt(plain_key.encode()).decode()

def decrypt_key(encrypted_key: str, machine_id: str = "default") -> str:
    if not encrypted_key:
        return ""
    try:
        key = _derive_key(machine_id)
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return ""

def get_machine_id() -> str:
    import platform
    import uuid
    from key_storage import get_storage_dir
    path = os.path.join(get_storage_dir(), "machine_id.txt")
    cached = ""
    try:
        with open(path, encoding="utf-8") as f:
            cached = f.read().strip()
    except Exception:
        cached = ""
    if cached:
        return cached
    system_info = f"{platform.node()}-{uuid.getnode()}"
    machine_id = hashlib.md5(system_info.encode()).hexdigest()
    try:
        os.makedirs(get_storage_dir(), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(machine_id)
    except Exception:
        pass
    return machine_id

def fetch_models(provider_name: str, api_key: str) -> list:
    provider = PROVIDERS.get(provider_name)
    if not provider:
        return []

    try:
        url = f"{provider['base_url']}/models"
        if provider_name == "Gemini":
            response = requests.get(url, headers={"x-goog-api-key": api_key}, timeout=10)
        else:
            headers = {
                provider['header_key']: f"{provider['header_prefix']}{api_key}"
            }
            response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            models = []
            if provider_name == "Gemini":
                for m in data.get("models", []):
                    name = m.get("name", "")
                    if name.startswith("models/"):
                        name = name[len("models/"):]
                    methods = m.get("supportedGenerationMethods", [])
                    if name and "generateContent" in methods:
                        models.append(name)
            elif "data" in data:
                for m in data["data"]:
                    model_id = m.get("id", "")
                    if provider_name == "OpenRouter" and not model_id.endswith(":free"):
                        continue
                    if model_id:
                        models.append(model_id)
            return sorted(models)
        return []
    except Exception:
        return []

def get_provider_config_key(provider_name: str) -> str:
    provider = PROVIDERS.get(provider_name)
    return provider["config_key"] if provider else ""

def get_chat_url(provider_name: str, model: str = "") -> str:
    provider = PROVIDERS.get(provider_name)
    if not provider:
        return ""
    if provider_name == "Gemini":
        return f"{provider['base_url']}/models/{model}:generateContent"
    return f"{provider['base_url']}/chat/completions"

def build_headers(provider_name: str, api_key: str) -> dict:
    provider = PROVIDERS.get(provider_name)
    if not provider:
        return {}
    headers = {"Content-Type": "application/json"}
    if provider_name == "Gemini":
        headers[provider['header_key']] = api_key
    else:
        headers[provider['header_key']] = f"{provider['header_prefix']}{api_key}"
    return headers


def check_model_health(provider_name: str, api_key: str, model: str) -> bool:
    url = get_chat_url(provider_name, model)
    headers = build_headers(provider_name, api_key)

    if provider_name == "Gemini":
        contents = [{"parts": [{"text": "hi"}]}]
        data = {"contents": contents, "generationConfig": {"maxOutputTokens": 1}}
    else:
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.status_code == 200
    except Exception:
        return False
