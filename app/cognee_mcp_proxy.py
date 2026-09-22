from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer


server = MCPServer(
    name="inneros-cognee-memory-fallback",
    title="InnerOS Cognee Shared Memory Fallback",
    description=(
        "Non-canonical compatibility MCP bridge for local tests only. "
        "The canonical runtime is inneros-cognee-mcp.service using cognee/cognee-mcp:main."
    ),
    version="0.1.0",
)


def _base_url() -> str:
    return os.getenv("COGNEE_SERVICE_URL", "https://api.cognee.ai").rstrip("/")


def _dataset() -> str:
    return os.getenv("COGNEE_DATASET", "inneros-personal-brain")


def _headers() -> dict[str, str]:
    api_key = os.getenv("COGNEE_API_KEY", "")
    if not api_key:
        raise RuntimeError("COGNEE_API_KEY is not configured")
    return {"X-Api-Key": api_key}


@server.tool(name="recall", description="Recall durable shared memory from Cognee.")
async def recall(query: str, top_k: int = 8) -> dict[str, Any]:
    payload = {
        "query": query[:1200],
        "datasets": [_dataset()],
        "top_k": max(1, min(top_k, 20)),
        "only_context": True,
        "verbose": True,
        "search_type": None,
    }
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        response = await client.post(
            f"{_base_url()}/api/v1/recall",
            headers=_headers(),
            json=payload,
        )
        if response.status_code == 422:
            legacy_payload = {
                "query": payload["query"],
                "datasets": payload["datasets"],
                "topK": payload["top_k"],
                "onlyContext": True,
                "verbose": True,
                "searchType": None,
            }
            response = await client.post(
                f"{_base_url()}/api/v1/recall",
                headers=_headers(),
                json=legacy_payload,
            )
        response.raise_for_status()
        rows = response.json()
    return {
        "provider": "cognee",
        "dataset": _dataset(),
        "rows": rows if isinstance(rows, list) else [rows],
    }


@server.tool(name="remember", description="Store a verified durable fact in Cognee shared memory.")
async def remember(text: str, node_set: str = "agent-memory") -> dict[str, Any]:
    safe_text = text[:4000]
    files = [
        ("raw_data", (None, safe_text)),
        ("datasetName", (None, _dataset())),
        ("run_in_background", (None, "true")),
        ("node_set", (None, node_set[:120])),
    ]
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        response = await client.post(
            f"{_base_url()}/api/v1/remember",
            headers=_headers(),
            files=files,
        )
        response.raise_for_status()
        body = response.json() if response.content else {"ok": True}
    return {"provider": "cognee", "dataset": _dataset(), "stored": True, "response": body}


@server.tool(name="forget", description="Request removal of memory from Cognee when supported by the tenant.")
async def forget(query: str) -> dict[str, Any]:
    payload = {"query": query[:1200], "datasets": [_dataset()]}
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        response = await client.post(
            f"{_base_url()}/api/v1/forget",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        body = response.json() if response.content else {"ok": True}
    return {"provider": "cognee", "dataset": _dataset(), "forgot": True, "response": body}


def main() -> None:
    server.run(
        "streamable-http",
        host=os.getenv("COGNEE_MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("COGNEE_MCP_FALLBACK_PORT", "8242")),
        streamable_http_path=os.getenv("COGNEE_MCP_PATH", "/mcp"),
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
