import requests
from .config import (
    ARK_API_KEY,
    ARK_ENDPOINT_ID,
    ARK_ENDPOINT_ID_SEEDREAM_5_LITE,
    ARK_ANALYSIS_ENDPOINT_ID,
    ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI,
    ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO,
)


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _resolve_analysis_endpoint(model: str) -> str:
    if model == "doubao-seed-2-0-mini":
        return ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI
    if model == "doubao-seed-2-0-pro":
        return ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO
    return ARK_ANALYSIS_ENDPOINT_ID


def _resolve_generation_endpoint(model: str) -> str:
    if model == "doubao-seedream-5.0-lite":
        return ARK_ENDPOINT_ID_SEEDREAM_5_LITE
    return ARK_ENDPOINT_ID


def chat_with_images(model: str, content: list) -> dict:
    endpoint_id = _resolve_analysis_endpoint(model)
    if not ARK_API_KEY or not endpoint_id:
        raise ApiError(500, "ARK_API_KEY or ARK_ANALYSIS_ENDPOINT_ID not configured")
    payload = {"model": endpoint_id, "messages": [{"role": "user", "content": content}]}
    headers = {"Authorization": f"Bearer {ARK_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(
            "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()
    except requests.HTTPError as error:
        detail = error.response.text if error.response is not None else str(error)
        status = error.response.status_code if error.response is not None else 500
        raise ApiError(status, f"Ark API Error: {detail}")
    except Exception as error:
        raise ApiError(500, str(error))


def generate_image(model: str, prompt: str, size: str = "2048x2048", image_urls=None) -> dict:
    endpoint_id = _resolve_generation_endpoint(model)
    if not ARK_API_KEY or not endpoint_id:
        raise ApiError(500, "Ark API Key or Endpoint ID not configured")
    payload = {"model": endpoint_id, "prompt": prompt, "size": size, "watermark": False}
    if image_urls:
        payload["image"] = image_urls[0]
    headers = {"Authorization": f"Bearer {ARK_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(
            "https://ark.cn-beijing.volces.com/api/v3/images/generations",
            headers=headers,
            json=payload,
            timeout=120,
        )
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()
    except requests.HTTPError as error:
        detail = error.response.text if error.response is not None else str(error)
        status = error.response.status_code if error.response is not None else 500
        raise ApiError(status, f"Ark API Error: {detail}")
    except Exception as error:
        raise ApiError(500, str(error))
