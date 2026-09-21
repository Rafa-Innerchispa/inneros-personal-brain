from __future__ import annotations

from strands import Agent, tool
from strands.models.openai import OpenAIModel


@tool
def evidence_marker(value: str = "ok") -> str:
    """Return a harmless evidence marker."""
    return value


def main() -> int:
    model = OpenAIModel(
        client_args={"api_key": "local", "base_url": "http://127.0.0.1:18000/v1"},
        model_id="QuantTrio/Qwen3-Coder-30B-A3B-Instruct-AWQ",
        params={"tool_choice": "none"},
    )
    agent = Agent(
        model=model,
        tools=[evidence_marker],
        system_prompt="Reply with exactly INNEROS_STRANDS_PRIMARY_OK and nothing else.",
    )
    result = str(agent("Connectivity smoke test. Do not call tools."))
    print(result)
    return 0 if "INNEROS_STRANDS_PRIMARY_OK" in result else 2


if __name__ == "__main__":
    raise SystemExit(main())
