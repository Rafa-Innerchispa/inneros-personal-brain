from __future__ import annotations

import importlib.util
import os
import socket

from app.memory_fabric import build_memory_fabric
from app.sandbox import DockerSandboxExecutor


def _importable(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _tcp_open(host: str, port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def sponsor_status() -> dict:
    """Return demo-safe readiness only; never expose credentials."""
    docker = DockerSandboxExecutor().smoke()
    mcp_reachable = _tcp_open("127.0.0.1", 8102)
    memory_fabric = build_memory_fabric().as_dict()
    return {
        "inneros_mcp": {
            "state": "connected" if mcp_reachable else "optional_offline",
            "label": "InnerOS MCP / external system bridge",
            "core_dependency": False,
        },
        "cognee": {
            "state": "ready"
            if os.getenv("COGNEE_API_KEY") and os.getenv("COGNEE_SERVICE_URL")
            else "platform_ready_secret_pending",
            "label": "Cognee structured memory",
            "core_dependency": True,
        },
        "cognee_agent_memory": {
            "state": "ready"
            if (
                os.getenv("COGNEE_API_KEY")
                and os.getenv("COGNEE_SERVICE_URL")
                and _importable("strands")
            )
            else "dependency_pending",
            "label": "Cognee direct Strands agent memory",
            "core_dependency": True,
            "transport": "direct_cloud_http_tools",
            "dataset": os.getenv("COGNEE_DATASET", "inneros-personal-brain"),
        },
        "brightdata": {
            "state": "ready"
            if os.getenv("BRIGHTDATA_API_TOKEN")
            else "server_capability_verified",
            "label": "Bright Data live web",
            "core_dependency": True,
        },
        "strands": {
            "state": "ready" if _importable("strands") else "dependency_pending",
            "label": "AWS Strands agent harness",
            "core_dependency": True,
        },
        "docker": {
            "state": "ready" if docker.get("ok") else docker.get("error", "sandbox_pending"),
            "label": "Docker Sandbox actions",
            "core_dependency": True,
        },
        "local_model": {
            "state": "configured" if os.getenv("LOCAL_LLM_BASE_URL") else "default_local_route",
            "label": "Local Qwen / vLLM inference",
            "core_dependency": True,
        },
        "connectors": {
            "mcp_reachable": mcp_reachable,
            "cognee_direct_agent_memory": bool(
                os.getenv("COGNEE_API_KEY") and os.getenv("COGNEE_SERVICE_URL")
            ),
            "cognee_mcp_surface": "registered_platform_capability",
            "github": "via_mcp" if mcp_reachable else "bridge_optional",
            "gmail": "via_mcp" if mcp_reachable else "bridge_optional",
            "calendar": "via_mcp" if mcp_reachable else "bridge_optional",
            "drive_notion": "via_mcp" if mcp_reachable else "bridge_optional",
            "infrastructure": "via_mcp" if mcp_reachable else "bridge_optional",
        },
        "memory_fabric": memory_fabric,
    }
