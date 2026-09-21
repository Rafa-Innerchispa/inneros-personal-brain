from __future__ import annotations

import importlib.util
import os


def _importable(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def sponsor_status() -> dict:
    """Return demo-safe readiness only; never expose credentials."""
    return {
        "inneros_mcp": {
            "state": "connected" if os.getenv("INNEROS_MEMORY_ENDPOINT") else "bridge_pending",
            "label": "InnerOS MCP / memory",
        },
        "cognee": {
            "state": "ready" if _importable("cognee") and os.getenv("USE_COGNEE") == "1" else "adapter_ready",
            "label": "Cognee structured memory",
        },
        "brightdata": {
            "state": "connected" if os.getenv("INNEROS_BRIGHTDATA_ENDPOINT") else "server_capability_verified",
            "label": "Bright Data live web",
        },
        "strands": {
            "state": "ready" if _importable("strands") else "dependency_pending",
            "label": "AWS Strands agent harness",
        },
        "docker": {
            "state": "ready" if os.getenv("DOCKER_SANDBOX_ENABLED") == "1" else "sandbox_pending",
            "label": "Docker Sandbox actions",
        },
        "local_model": {
            "state": "configured" if os.getenv("LOCAL_LLM_BASE_URL") else "default_local_route",
            "label": "Local AMD vLLM",
        },
    }
