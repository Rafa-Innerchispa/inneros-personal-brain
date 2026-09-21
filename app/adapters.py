from __future__ import annotations

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
    """Reuse the existing Ralphi/InnerOS memory surface without copying data.

    Expected server-side contract:
      POST /search   {"query": "...", "limit": 8}
      POST /remember {"text": "...", "metadata": {...}}
    """

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


class CogneeMemoryAdapter:
    """Optional local/self-hosted Cognee adapter."""

    def __init__(self, dataset_name: str = "inneros-personal-brain") -> None:
        self.dataset_name = dataset_name

    async def search(self, query: str, limit: int = 8) -> list[Evidence]:
        import cognee

        results = await cognee.search(query_text=query)
        return [
            Evidence(source="cognee", summary=str(item), metadata={"dataset": self.dataset_name})
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
