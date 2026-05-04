import os

import requests

_api_key = None
_region = None


def _get_config():
    global _api_key, _region
    if _api_key is None:
        _api_key = os.getenv("BEDROCK_API_KEY", "")
        _region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    return _api_key, _region


def invoke_model(model_id: str, body: dict) -> dict:
    api_key, region = _get_config()
    url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_id}/invoke"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


def converse(model_id: str, messages: list, system: list, inference_config: dict) -> dict:
    api_key, region = _get_config()
    url = f"https://bedrock-runtime.{region}.amazonaws.com/model/{model_id}/converse"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "messages": messages,
        "system": system,
        "inferenceConfig": inference_config,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()
