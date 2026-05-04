import logging
import random
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Prompt registry — controls which version is active in production,
# supports A/B traffic splitting, and allows instant rollback via config.
# ---------------------------------------------------------------------------

_registry = {
    "active_version": "v1",
    "ab_test": None,  # set to {"control": "v1", "candidate": "v2", "traffic_pct": 10} to enable
}


def get_registry() -> dict:
    return dict(_registry)


def set_active_version(version: str):
    if not (PROMPTS_DIR / f"{version}.yaml").exists():
        raise FileNotFoundError(f"Prompt version '{version}' not found")
    _registry["active_version"] = version
    _registry["ab_test"] = None
    logger.info("Prompt active version set to %s", version)


def start_ab_test(control: str, candidate: str, traffic_pct: int = 10):
    for v in (control, candidate):
        if not (PROMPTS_DIR / f"{v}.yaml").exists():
            raise FileNotFoundError(f"Prompt version '{v}' not found")
    if not 1 <= traffic_pct <= 99:
        raise ValueError("traffic_pct must be between 1 and 99")
    _registry["ab_test"] = {
        "control": control,
        "candidate": candidate,
        "traffic_pct": traffic_pct,
    }
    _registry["active_version"] = control
    logger.info("A/B test started: %s (control) vs %s (%d%% traffic)", control, candidate, traffic_pct)


def stop_ab_test():
    _registry["ab_test"] = None
    logger.info("A/B test stopped, active version: %s", _registry["active_version"])


def resolve_version() -> str:
    ab = _registry["ab_test"]
    if ab:
        if random.randint(1, 100) <= ab["traffic_pct"]:
            return ab["candidate"]
        return ab["control"]
    return _registry["active_version"]


# ---------------------------------------------------------------------------
# Prompt loading and message building
# ---------------------------------------------------------------------------

def load_prompt(version: str) -> dict:
    path = PROMPTS_DIR / f"{version}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt version '{version}' not found at {path}")
    return _load_yaml(path)


def get_available_versions() -> list[str]:
    return sorted(p.stem for p in PROMPTS_DIR.glob("v*.yaml"))


def build_messages(question: str, chunks: list[dict], version: str | None = None) -> tuple[list, list, dict, str]:
    """Build Bedrock converse API arguments from prompt template + dynamic content.

    If version is None, the registry resolves it (active version or A/B split).
    Returns (messages, system, inference_config, prompt_version).
    """
    if version is None:
        version = resolve_version()

    prompt = load_prompt(version)
    prompt_version = prompt["version"]

    system = [{"text": prompt["system_prompt"].rstrip()}]

    few_shot_messages = []
    for entry in prompt.get("few_shot", []):
        few_shot_messages.append({
            "role": entry["role"],
            "content": [{"text": entry["text"]}],
        })

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[{i}] Patient: {chunk['patient_name']} | Section: {chunk['section_name']}\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)
    user_message = f"Document sections:\n\n{context}\n\nQuestion: {question}"

    messages = few_shot_messages + [
        {"role": "user", "content": [{"text": user_message}]},
    ]

    config = prompt.get("config", {})
    inference_config = {
        "maxTokens": config.get("max_tokens", 1024),
        "temperature": config.get("temperature", 0.0),
    }

    return messages, system, inference_config, prompt_version


def get_model_id(version: str | None = None) -> str:
    if version is None:
        version = resolve_version()
    prompt = load_prompt(version)
    return prompt.get("config", {}).get("model_id", "us.anthropic.claude-sonnet-4-20250514-v1:0")
