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
