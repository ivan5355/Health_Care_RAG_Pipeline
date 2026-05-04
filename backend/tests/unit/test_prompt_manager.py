import pytest

from services.prompt_manager import (
    _registry,
    build_messages,
    get_available_versions,
    get_model_id,
    load_prompt,
    resolve_version,
)


def test_load_prompt_v1():
    prompt = load_prompt("v1")
    assert "version" in prompt
    assert "system_prompt" in prompt
    assert "config" in prompt
    assert "few_shot" in prompt


def test_load_prompt_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_prompt("v999")


def test_get_available_versions():
    versions = get_available_versions()
    assert "v1" in versions


def test_resolve_version_default():
    _registry["ab_test"] = None
    _registry["active_version"] = "v1"
    assert resolve_version() == "v1"


def test_resolve_version_ab_test():
    _registry["ab_test"] = {"control": "v1", "candidate": "v1", "traffic_pct": 50}
    _registry["active_version"] = "v1"
    result = resolve_version()
    assert result == "v1"
    _registry["ab_test"] = None


def test_get_model_id():
    model_id = get_model_id("v1")
    assert "claude" in model_id or "anthropic" in model_id


def test_build_messages_structure():
    chunks = [
        {"patient_name": "WALKER, JAMES R", "section_name": "TOTALS", "text": "Total Billed: $687.00"},
    ]
    messages, system, inference_config, version = build_messages("What is the total?", chunks, "v1")
    assert isinstance(messages, list)
    assert isinstance(system, list)
    assert len(system) > 0
    assert "text" in system[0]
    assert isinstance(inference_config, dict)
    assert "maxTokens" in inference_config
    assert "temperature" in inference_config
    assert version is not None

    last_msg = messages[-1]
    assert last_msg["role"] == "user"
    assert "Total Billed: $687.00" in last_msg["content"][0]["text"]
    assert "What is the total?" in last_msg["content"][0]["text"]
