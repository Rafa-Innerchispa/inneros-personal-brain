from __future__ import annotations

import importlib.util
import os
import socket
from urllib.parse import urlparse

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


def _url_tcp_open(url: str, timeout: float = 0.35) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return _tcp_open(host, port, timeout=timeout)


def sponsor_status() -> dict:
    """Return demo-safe readiness only; never expose credentials."""
    docker = DockerSandboxExecutor().smoke()
    mcp_reachable = _tcp_open("127.0.0.1", 8102)
    cognee_mcp_reachable = _tcp_open("127.0.0.1", int(os.getenv("COGNEE_MCP_PORT", "8241")))
    voiceops_reachable = _tcp_open("127.0.0.1", int(os.getenv("VOICEOPS_GATEWAY_PORT", "8200")))
    llm_url = os.getenv("LOCAL_LLM_BASE_URL", "")
    local_model_ready = bool(llm_url and _url_tcp_open(llm_url))
    memory_fabric = build_memory_fabric().as_dict()
    brightdata_rest_ready = bool(
        os.getenv("BRIGHTDATA_API_KEY")
        and os.getenv("BRIGHTDATA_SERP_ZONE", os.getenv("BRIGHTDATA_ZONE", "inneros"))
    )
    brightdata_mcp_configured = bool(os.getenv("BRIGHTDATA_API_TOKEN"))
    brightdata_auth_failed = os.getenv("BRIGHTDATA_MCP_AUTH_FAILED") == "1"
    brightdata_ready = brightdata_rest_ready or (brightdata_mcp_configured and not brightdata_auth_failed)
    return {
        "inneros_mcp": {
            "state": "connected" if mcp_reachable else "optional_offline",
            "label": "InnerOS MCP / external system bridge",
            "core_dependency": False,
        },
        "cognee": {
            "state": "ready"
            if (cognee_mcp_reachable or os.getenv("COGNEE_LIVE_VERIFIED") == "1")
            else "configured" if os.getenv("COGNEE_API_KEY") else "platform_ready_secret_pending",
            "label": "Cognee structured memory",
            "core_dependency": True,
        },
        "cognee_agent_memory": {
            "state": "ready"
            if (
                cognee_mcp_reachable
                and _importable("strands")
            )
            else "configured"
            if (
                os.getenv("COGNEE_API_KEY")
                and _importable("strands")
            )
            else "dependency_pending",
            "label": "Cognee direct Strands agent memory",
            "core_dependency": True,
            "transport": "official_local_mcp",
            "dataset": os.getenv("COGNEE_DATASET", "inneros-personal-brain"),
        },
        "brightdata": {
            "state": "ready"
            if brightdata_ready
            else "auth_required" if brightdata_auth_failed else "server_capability_verified",
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
            "state": "ready" if local_model_ready else "configured" if os.getenv("LOCAL_LLM_BASE_URL") else "default_local_route",
            "label": "Local Qwen / vLLM inference",
            "core_dependency": True,
        },
        "voiceops": {
            "state": "ready" if voiceops_reachable else "configured",
            "label": "Local VoiceOps speech input/output",
            "core_dependency": False,
            "transport": "local_gateway",
        },
        "connectors": {
            "mcp_reachable": mcp_reachable,
            "cognee_direct_agent_memory": cognee_mcp_reachable,
            "cognee_mcp_surface": "ready" if cognee_mcp_reachable else "registered_platform_capability",
            "github": "via_mcp" if mcp_reachable else "bridge_optional",
            "gmail": "via_mcp" if mcp_reachable else "bridge_optional",
            "calendar": "via_mcp" if mcp_reachable else "bridge_optional",
            "drive_notion": "via_mcp" if mcp_reachable else "bridge_optional",
            "infrastructure": "via_mcp" if mcp_reachable else "bridge_optional",
        },
        "memory_fabric": memory_fabric,
    }
