import os
import requests
from typing import Optional

MAIN_URL = "http://main:8000/api/v1/"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "changeme")
ADMIN_TOKEN = f"Admin-Key {ADMIN_API_KEY}"


def request_post(
    endpoint: str,
    data: dict,
    headers: dict,
    use_json: bool = False,
    files: list = None,
    return_status: bool = False,
    method: Optional[str] = "POST",
):
    url = f"{MAIN_URL}{endpoint}"
    try:
        request_method = getattr(requests, method.lower())
        if files:
            response = request_method(url, files=files, headers=headers)
        elif use_json:
            response = request_method(url, json=data, headers=headers)
        else:
            response = request_method(url, data=data, headers=headers)

        if response.status_code == 200:
            return (
                (response.status_code, response.json())
                if return_status
                else response.json()
            )

        print(f"[ERROR] POST {url}: {response.status_code} - {response.text}")
        return (response.status_code, None) if return_status else False

    except Exception as e:
        print(f"[Exception] Request to {url} failed: {e}")
        return (None, None) if return_status else False


def create_api_key():
    payload = {"name": "mcp-server-script", "is_active": True}
    headers = {
        "Content-Type": "application/json",
        "Authorization": ADMIN_TOKEN,
    }
    result = request_post("api-key", payload, headers, use_json=True)
    if not result or not result.get("key"):
        return None
    api_key = result.get("key")
    return f"API-Key {api_key}"


def create_knowledge_base(token: str, title: str, description: str):
    payload = {"name": title, "description": description}
    headers = {"Content-Type": "application/json", "Authorization": token}
    result = request_post("knowledge-base", payload, headers, use_json=True)
    return result.get("id") if result else False


def upload_documents(
    token: str,
    kb_id: int,
    file_paths: list,
):
    endpoint = f"knowledge-base/{kb_id}/documents/upload"
    headers = {"Authorization": token}

    files = [
        (
            "files",
            (os.path.basename(path), open(path, "rb"), "application/pdf"),
        )
        for path in file_paths
    ]

    try:
        result = request_post(endpoint, data={}, headers=headers, files=files)
        return result
    finally:
        for f in files:
            f[1][1].close()  # Close file handles


def process_documents(
    token: str,
    kb_id: int,
    upload_results: list,
):
    endpoint = f"knowledge-base/{kb_id}/documents/process"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    return request_post(endpoint, upload_results, headers, use_json=True)
