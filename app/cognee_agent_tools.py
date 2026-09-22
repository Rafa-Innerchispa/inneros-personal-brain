from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class CogneeAgentMemoryTools:
    """Direct Cognee Cloud tools for a Strands agent.

    This is intentionally independent from Ralphi MCP. The agent talks to the
    same Cognee Cloud dataset used by the Personal Brain, so memory survives
    sessions and is shared with other Cognee clients/plugins.
    """

    base_url: str = field(default_factory=lambda: os.getenv("COGNEE_SERVICE_URL", "https://api.cognee.ai").rstrip("/"))
    api_key: str = field(default_factory=lambda: os.getenv("COGNEE_API_KEY", ""))
    dataset: str = field(default_factory=lambda: os.getenv("COGNEE_DATASET", "inneros-personal-brain"))
    recall_calls: int = 0
    remember_calls: int = 0

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.api_key}

    def build(self) -> list[Any]:
        if not self.ready:
            return []

        from strands import tool

        tracker = self

        @tool
        def cognee_recall(query_text: str) -> str:
            """Recall durable shared memory from Cognee.

            Use this before answering questions about prior projects, decisions,
            preferences, architecture, previous outcomes, or anything that may
            have happened in an earlier session.

            Args:
                query_text: Natural-language memory query.
            """
            tracker.recall_calls += 1
            payload = {
                "search_type": None,
                "datasets": [tracker.dataset],
                "query": query_text[:1200],
                "top_k": 8,
                "only_context": True,
                "verbose": True,
            }
            with httpx.Client(timeout=45, follow_redirects=True) as client:
                response = client.post(
                    tracker.base_url + "/api/v1/recall",
                    headers=tracker._headers(),
                    json=payload,
                )
                if response.status_code == 422:
                    legacy_payload = {
                        "searchType": None,
                        "datasets": [tracker.dataset],
                        "query": query_text[:1200],
                        "topK": 8,
                        "onlyContext": True,
                        "verbose": True,
                    }
                    response = client.post(
                        tracker.base_url + "/api/v1/recall",
                        headers=tracker._headers(),
                        json=legacy_payload,
                    )
                response.raise_for_status()
                rows = response.json()
            if not isinstance(rows, list):
                rows = [rows]
            texts = []
            for row in rows[:8]:
                if isinstance(row, dict):
                    texts.append(str(row.get("text") or row.get("content") or row))
                else:
                    texts.append(str(row))
            return json.dumps(
                {
                    "provider": "cognee",
                    "dataset": tracker.dataset,
                    "count": len(texts),
                    "memory": texts,
                },
                ensure_ascii=False,
            )

        @tool
        def cognee_remember(data: str) -> str:
            """Store a durable verified fact or outcome in shared Cognee memory.

            Use only for durable facts, decisions, verified outcomes, or explicit
            user requests to remember something. Do not store credentials,
            speculative claims, or raw untrusted web content.

            Args:
                data: Verified information to persist.
            """
            tracker.remember_calls += 1
            safe = data[:4000]
            files = [
                ("raw_data", (None, safe)),
                ("datasetName", (None, tracker.dataset)),
                ("run_in_background", (None, "true")),
                ("node_set", (None, "strands-agent-memory")),
            ]
            with httpx.Client(timeout=45, follow_redirects=True) as client:
                response = client.post(
                    tracker.base_url + "/api/v1/remember",
                    headers=tracker._headers(),
                    files=files,
                )
                response.raise_for_status()
            return json.dumps(
                {
                    "ok": True,
                    "provider": "cognee",
                    "dataset": tracker.dataset,
                    "stored": True,
                }
            )

        return [cognee_recall, cognee_remember]

    def usage(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "provider": "cognee",
            "dataset": self.dataset,
            "recall_calls": self.recall_calls,
            "remember_calls": self.remember_calls,
            "direct_agent_tools": True,
        }


@dataclass
class CogneeMemoryStore:
    """Small Strands MemoryManager-compatible Cognee store.

    The installed Strands SDK version may expose different MemoryManager entry
    points, so this class keeps the stable surface we need: search/add against
    the same Cognee dataset. PersonalBrain uses it for safe automatic memory
    injection evidence and can be passed to a native MemoryManager where the SDK
    supports compatible stores.
    """

    base_url: str = field(default_factory=lambda: os.getenv("COGNEE_SERVICE_URL", "https://api.cognee.ai").rstrip("/"))
    api_key: str = field(default_factory=lambda: os.getenv("COGNEE_API_KEY", ""))
    dataset: str = field(default_factory=lambda: os.getenv("COGNEE_DATASET", "inneros-personal-brain"))
    injected_count: int = 0
    add_count: int = 0

    @property
    def ready(self) -> bool:
        return bool(self.base_url and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.api_key}

    async def search(self, query: str, limit: int = 6) -> list[str]:
        if not self.ready:
            return []
        payload = {
            "search_type": None,
            "datasets": [self.dataset],
            "query": query[:1200],
            "top_k": max(1, min(limit, 12)),
            "only_context": True,
            "verbose": True,
        }
        async with httpx.AsyncClient(timeout=35, follow_redirects=True) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/recall",
                headers=self._headers(),
                json=payload,
            )
            if response.status_code == 422:
                legacy_payload = {
                    "searchType": None,
                    "datasets": payload["datasets"],
                    "query": payload["query"],
                    "topK": payload["top_k"],
                    "onlyContext": True,
                    "verbose": True,
                }
                response = await client.post(
                    f"{self.base_url}/api/v1/recall",
                    headers=self._headers(),
                    json=legacy_payload,
                )
            response.raise_for_status()
            rows = response.json()
        if not isinstance(rows, list):
            rows = [rows]
        memories: list[str] = []
        for row in rows[:limit]:
            if isinstance(row, dict):
                memories.append(str(row.get("text") or row.get("content") or row))
            else:
                memories.append(str(row))
        self.injected_count += len(memories)
        return memories

    async def add(self, text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.ready:
            return {"ok": False, "reason": "cognee_credentials_missing", "dataset": self.dataset}
        envelope = text if not metadata else json.dumps(
            {"text": text[:4000], "metadata": metadata},
            ensure_ascii=False,
            default=str,
        )
        files = [
            ("raw_data", (None, envelope[:4000])),
            ("datasetName", (None, self.dataset)),
            ("run_in_background", (None, "true")),
            ("node_set", (None, "strands-memory-manager")),
        ]
        async with httpx.AsyncClient(timeout=35, follow_redirects=True) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/remember",
                headers=self._headers(),
                files=files,
            )
            response.raise_for_status()
        self.add_count += 1
        return {"ok": True, "provider": "cognee", "dataset": self.dataset, "stored": True}

    def status(self) -> dict[str, Any]:
        try:
            import strands  # noqa: F401
            sdk_present = True
        except Exception:
            sdk_present = False
        return {
            "ready": self.ready,
            "sdk_present": sdk_present,
            "dataset": self.dataset,
            "injected_count": self.injected_count,
            "add_count": self.add_count,
            "compatible_surface": "search/add",
        }
