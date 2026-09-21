from __future__ import annotations

import importlib.util
import os

from app.sandbox import DockerSandboxExecutor


def _importable(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def sponsor_status() -> dict:
    """Return demo-safe readiness only; never expose credentials."""
    docker = DockerSandboxExecutor().smoke()
    return {
        "inneros_mcp": {
            "state": "connected" if os.getenv("INNEROS_MEMORY_ENDPOINT") else "bridge_pending",
            "label": "InnerOS MCP / memory",
        },
        "cognee": {
            "state": "ready"
            if os.getenv("COGNEE_API_KEY") and os.getenv("COGNEE_SERVICE_URL")
            else "platform_ready_secret_pending",
            "label": "Cognee structured memory",
        },
        "brightdata": {
            "state": "ready"
            if os.getenv("BRIGHTDATA_API_TOKEN")
            else (
                "connected"
                if os.getenv("INNEROS_BRIGHTDATA_ENDPOINT")
                else "server_capability_verified"
            ),
            "label": "Bright Data live web",
        },
        "strands": {
            "state": "ready" if _importable("strands") else "dependency_pending",
            "label": "AWS Strands agent harness",
        },
        "docker": {
            "state": "ready" if docker.get("ok") else docker.get("error", "sandbox_pending"),
            "label": "Docker Sandbox actions",
        },
        "local_model": {
            "state": "configured" if os.getenv("LOCAL_LLM_BASE_URL") else "default_local_route",
            "label": "Local AMD vLLM",
        },
    }
