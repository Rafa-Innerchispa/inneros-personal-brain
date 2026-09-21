from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.models import Evidence


class MemoryAdapter(Protocol):
    async def search(self, query: str, limit: int = 8) -> list[Evidence]: ...
    async def remember(self, text: str, metadata: dict | None = None) -> None: ...


class WebAdapter(Protocol):
    async def search(self, query: str, limit: int = 5) -> list[Evidence]: ...


@dataclass
class DemoMemoryAdapter:
    seed: list[str]

    async def search(self, query: str, limit: int = 8) -> list[Evidence]:
        terms = {t.lower() for t in query.split() if len(t) > 3}
        ranked = sorted(
            self.seed,
            key=lambda item: sum(term in item.lower() for term in terms),
            reverse=True,
        )
        return [
            Evidence(source="inneros-memory", summary=item, metadata={"mode": "demo-local"})
            for item in ranked[:limit]
        ]

    async def remember(self, text: str, metadata: dict | None = None) -> None:
        self.seed.append(text)


class InnerOSMemoryAdapter:
    """Reuse the existing Ralphi/InnerOS memory surface without copying data."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("INNEROS_MEMORY_ENDPOINT", "").rstrip("/")
        self.token = os.getenv("INNEROS_CAPABILITY_TOKEN", "")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def search(self, query: str, limit: int = 8) -> list[Evidence]:
        if not self.endpoint:
            return []
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.endpoint}/search",
                json={"query": query, "limit": limit},
                headers=self._headers(),
            )
            response.raise_for_status()
            payload = response.json()

        items = payload.get("results", payload if isinstance(payload, list) else [])
        evidence: list[Evidence] = []
        for item in items[:limit]:
            if isinstance(item, dict):
                summary = item.get("text") or item.get("summary") or item.get("title") or str(item)
                source = item.get("source", "inneros-memory")
                metadata = {k: v for k, v in item.items() if k not in {"text", "summary"}}
            else:
                summary, source, metadata = str(item), "inneros-memory", {}
            evidence.append(Evidence(source=source, summary=summary, metadata=metadata))
        return evidence

    async def remember(self, text: str, metadata: dict | None = None) -> None:
        if not self.endpoint:
            return
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.endpoint}/remember",
                json={"text": text, "metadata": metadata or {}},
                headers=self._headers(),
            )
            response.raise_for_status()


class CogneeCloudMemoryAdapter:
    """Live Cognee Cloud memory through the tenant's documented HTTP contract."""

    def __init__(self) -> None:
        self.base = os.getenv("COGNEE_SERVICE_URL", "").rstrip("/")
        self.key = os.getenv("COGNEE_API_KEY", "")
        self.dataset = os.getenv("COGNEE_DATASET", "inneros-personal-brain")

    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.key}

    async def search(self, query: str, limit: int = 8) -> list[Evidence]:
        if not self.base or not self.key:
            return []
        payload = {
            "searchType": None,
            "datasets": [self.dataset],
            "query": query,
            "topK": max(1, min(limit, 20)),
            "onlyContext": True,
            "verbose": True,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base}/api/v1/recall",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            rows = response.json()
        if not isinstance(rows, list):
            rows = [rows]
        return [
            Evidence(
                source="cognee",
                summary=str(row.get("text") if isinstance(row, dict) else row),
                metadata={
                    "dataset": self.dataset,
                    "search_type": row.get("search_type") if isinstance(row, dict) else None,
                    "live": True,
                },
            )
            for row in rows[:limit]
        ]

    async def remember(self, text: str, metadata: dict | None = None) -> None:
        if not self.base or not self.key:
            return
        envelope = text if not metadata else json.dumps(
            {"text": text, "metadata": metadata},
            ensure_ascii=False,
            default=str,
        )
        files = [
            ("raw_data", (None, envelope)),
            ("datasetName", (None, self.dataset)),
            ("run_in_background", (None, "true")),
            ("node_set", (None, "personal-brain-demo")),
        ]
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base}/api/v1/remember",
                headers=self._headers(),
                files=files,
            )
            response.raise_for_status()


class CogneeMemoryAdapter:
    """Optional local/self-hosted Cognee SDK adapter."""

    def __init__(self, dataset_name: str = "inneros-personal-brain") -> None:
        self.dataset_name = dataset_name

    async def search(self, query: str, limit: int = 8) -> list[Evidence]:
        import cognee
        results = await cognee.search(query_text=query)
        return [
            Evidence(source="cognee-local", summary=str(item), metadata={"dataset": self.dataset_name})
            for item in list(results)[:limit]
        ]

    async def remember(self, text: str, metadata: dict | None = None) -> None:
        import cognee
        await cognee.add(text, dataset_name=self.dataset_name)
        await cognee.cognify()


class BrightDataAdapter:
    """Consume Bright Data only through the server-side InnerOS capability."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("INNEROS_BRIGHTDATA_ENDPOINT", "").rstrip("/")
        self.token = os.getenv("INNEROS_CAPABILITY_TOKEN", "")

    async def search(self, query: str, limit: int = 5) -> list[Evidence]:
        if not self.endpoint:
            return []
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.endpoint}/search",
                json={"query": query, "limit": limit},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
        items = payload.get("results", payload if isinstance(payload, list) else [])
        return [
            Evidence(source="brightdata", summary=str(item), metadata={"live": True})
            for item in items[:limit]
        ]
