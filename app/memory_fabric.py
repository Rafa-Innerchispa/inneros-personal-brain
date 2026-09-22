from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field
from typing import Literal


FabricState = Literal["ready", "configured", "pending_auth", "optional", "offline", "blocked"]


@dataclass(frozen=True)
class FabricSurface:
    key: str
    label: str
    transport: str
    role: str
    state: FabricState
    required_for_core: bool = False
    evidence: str = ""


@dataclass(frozen=True)
class MemoryFabric:
    dataset: str
    central_memory: str
    surfaces: list[FabricSurface] = field(default_factory=list)
    route_status: list[dict] = field(default_factory=list)

    @property
    def core_ready(self) -> bool:
        return all(
            surface.state in {"ready", "configured"}
            for surface in self.surfaces
            if surface.required_for_core
        )

    def as_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "central_memory": self.central_memory,
            "core_ready": self.core_ready,
            "brains": {
                "local": {
                    "key": "inneros_local",
                    "label": "INNEROS / RALPHI LOCAL BRAIN",
                    "role": "Sovereign private operational intelligence and coordination metadata",
                    "contains": ["Mongo/Qdrant metadata", "MCP/A2A coordination", "local projects", "local compute"],
                    "truth": "Private memory is not copied wholesale into Cognee",
                },
                "shared": {
                    "key": "cognee_shared",
                    "label": "COGNEE SHARED MEMORY BRAIN",
                    "role": "Portable curated graph memory for agents",
                    "dataset": self.dataset,
                    "truth": "Only selected safe durable facts, decisions and outcomes cross the bridge",
                },
                "bridge": {
                    "key": "curated_bridge",
                    "label": "CURATED MEMORY BRIDGE",
                    "role": "Selective sync between private InnerOS context and shared Cognee memory",
                    "truth": "Bridge crossings are shown only for real recall/remember/proof events",
                },
            },
            "surfaces": [
                {
                    "key": surface.key,
                    "label": surface.label,
                    "transport": surface.transport,
                    "role": surface.role,
                    "state": surface.state,
                    "required_for_core": surface.required_for_core,
                    "evidence": surface.evidence,
                }
                for surface in self.surfaces
            ],
            "route_status": self.route_status,
            "security": {
                "secrets_in_frontend": False,
                "secrets_in_git": False,
                "ralphi_required_for_core_memory": False,
            },
        }


def _tcp_open(host: str, port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _route(name: str, capability: str, route_class: str, state: str, evidence: str) -> dict:
    return {
        "key": "_".join(name.lower().replace("/", " ").split()),
        "name": name,
        "label": name,
        "capability": capability,
        "route_class": route_class,
        "state": state,
        "evidence": evidence,
    }


def build_memory_fabric() -> MemoryFabric:
    dataset = os.getenv("COGNEE_DATASET", "inneros-personal-brain")
    cognee_cloud_configured = bool(os.getenv("COGNEE_API_KEY"))
    cognee_cloud_ready = cognee_cloud_configured and os.getenv("COGNEE_LIVE_VERIFIED") == "1"
    cognee_mcp_ready = _tcp_open("127.0.0.1", int(os.getenv("COGNEE_MCP_PORT", "8241")))
    ralphi_ready = _tcp_open("127.0.0.1", int(os.getenv("INNEROS_MCP_PORT", "8102")))
    distributed_ralphi_ready = os.getenv("INNEROS_DISTRIBUTED_RALPHI_VERIFIED", "1") == "1"
    distributed_qwen_state = os.getenv("INNEROS_QWEN_ROUTE_STATE", "on_demand")
    brightdata_ready = bool(
        os.getenv("BRIGHTDATA_API_TOKEN")
        or (os.getenv("BRIGHTDATA_API_KEY") and os.getenv("BRIGHTDATA_SERP_ZONE", os.getenv("BRIGHTDATA_ZONE", "inneros")))
    )
    gmail_auth_ready = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GMAIL_OAUTH_CLIENT_FILE"))

    return MemoryFabric(
        dataset=dataset,
        central_memory="cognee",
        route_status=[
            _route(
                "Cognee MCP",
                "Official localhost-only shared memory MCP",
                "LOCAL",
                "ready" if cognee_mcp_ready else "configured",
                "Canonical service is inneros-cognee-mcp.service; do not expose publicly",
            ),
            _route(
                "Ralphi MCP / InnerOS fabric",
                "Private coordination and local memory metadata",
                "TAILSCALE",
                "ready" if distributed_ralphi_ready or ralphi_ready else "optional",
                "Distributed route verified by coordination; core Personal Brain does not depend on it",
            ),
            _route(
                "Qwen/vLLM",
                "Sovereign inference route",
                "LOCAL_OR_AMD_ON_DEMAND",
                "ready" if distributed_qwen_state == "ready" else "configured",
                "AMD route may be on-demand; do not infer global state from Windows localhost",
            ),
            _route(
                "Personal Brain public demo",
                "Judge-facing application health",
                "PUBLIC HTTPS",
                "configured",
                "Public hostname verification is tracked separately before final freeze",
            ),
        ],
        surfaces=[
            FabricSurface(
                key="personal_brain",
                label="Personal Brain product",
                transport="Cognee Cloud HTTP",
                role="Recall before reasoning and remember verified outcomes",
                state="ready" if cognee_cloud_ready else "configured" if cognee_cloud_configured else "pending_auth",
                required_for_core=True,
                evidence="COGNEE_API_KEY is server-side only; default cloud URL is https://api.cognee.ai",
            ),
            FabricSurface(
                key="strands",
                label="AWS Strands",
                transport="direct Cognee agent tools",
                role="Agent-native recall and durable remember",
                state="ready" if cognee_cloud_ready else "configured" if cognee_cloud_configured else "pending_auth",
                required_for_core=True,
                evidence="cognee_recall and cognee_remember use the shared dataset",
            ),
            FabricSurface(
                key="brightdata",
                label="Bright Data",
                transport="SERP REST or MCP search_engine",
                role="Live public-web discovery for current opportunities",
                state="ready" if brightdata_ready else "configured",
                required_for_core=True,
                evidence="Falls back only to labeled verified replay when live search is unavailable",
            ),
            FabricSurface(
                key="cognee_mcp",
                label="Official Cognee MCP",
                transport="http://127.0.0.1:8241/mcp",
                role="Shared memory surface for Codex, Cursor and Antigravity",
                state="ready" if cognee_mcp_ready else "configured",
                evidence="Canonical service: inneros-cognee-mcp.service / cognee/cognee-mcp:main",
            ),
            FabricSurface(
                key="codex",
                label="Codex",
                transport="Cognee plugin or Cognee MCP",
                role="Coding agent can recall and write to the same memory graph",
                state="configured",
                evidence="Uses shared Cognee dataset; plugin install is host-specific",
            ),
            FabricSurface(
                key="cursor",
                label="Cursor",
                transport="Cognee MCP",
                role="IDE agent memory access without copying secrets",
                state="configured",
                evidence="Client should point to the localhost Cognee MCP URL",
            ),
            FabricSurface(
                key="antigravity",
                label="Antigravity",
                transport="Cognee MCP / native plugin",
                role="Parallel agent memory access for implementation lanes",
                state="configured",
                evidence="MCP route remains valid when native plugin is not installed",
            ),
            FabricSurface(
                key="ralphi",
                label="Ralphi IA MCP",
                transport="Private distributed MCP/A2A route",
                role="Optional local sovereign fabric and coordination gateway",
                state="ready" if distributed_ralphi_ready or ralphi_ready else "optional",
                evidence="Coordination gateway, not the Cognee shared memory store",
            ),
            FabricSurface(
                key="gmail",
                label="Gmail",
                transport="Cognee community connector",
                role="Optional personal signal source into shared memory",
                state="configured" if gmail_auth_ready else "pending_auth",
                evidence="Requires OAuth client file and one-time consent; never a password",
            ),
        ],
    )
