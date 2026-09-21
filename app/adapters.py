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


class CogneeMemoryAdapter:
    """Optional local/self-hosted Cognee adapter.

    The import is lazy so the app still runs before Cognee is installed.
    """

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
    """Adapter for an InnerOS server-side Bright Data capability endpoint.

    The browser/app never receives the Bright Data API token.
    """

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
