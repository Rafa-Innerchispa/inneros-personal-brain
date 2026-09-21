from __future__ import annotations

import os

from strands import Agent, tool
from strands.models.openai import OpenAIModel


@tool
def evidence_marker(value: str = "ok") -> str:
    """Return a harmless evidence marker.

    Args:
        value: Marker value.
    """
    return value


def main() -> int:
    model_id = os.getenv(
        "LOCAL_LLM_MODEL",
        "QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
    )
    base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8000/v1")

    model = OpenAIModel(
        client_args={"api_key": "local", "base_url": base_url},
        model_id=model_id,
    )
    agent = Agent(
        model=model,
        tools=[evidence_marker],
        system_prompt="Reply with exactly INNEROS_STRANDS_VLLM_OK and nothing else.",
    )
    result = str(agent("Connectivity smoke test. Do not call tools."))
    print(result)
    return 0 if "INNEROS_STRANDS_VLLM_OK" in result else 2


if __name__ == "__main__":
    raise SystemExit(main())
