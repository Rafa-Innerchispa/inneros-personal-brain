from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
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
        self.base = os.getenv("COGNEE_SERVICE_URL", "https://api.cognee.ai").rstrip("/")
        self.key = os.getenv("COGNEE_API_KEY", "")
        self.dataset = os.getenv("COGNEE_DATASET", "inneros-personal-brain")

    def _headers(self) -> dict[str, str]:
        return {"X-Api-Key": self.key}

    async def search(self, query: str, limit: int = 8) -> list[Evidence]:
        if not self.base or not self.key:
            return []
        payload = {
            "search_type": None,
            "datasets": [self.dataset],
            "query": query,
            "top_k": max(1, min(limit, 20)),
            "only_context": True,
            "verbose": True,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base}/api/v1/recall",
                headers=self._headers(),
                json=payload,
            )
            if response.status_code == 422:
                legacy_payload = {
                    "searchType": None,
                    "datasets": [self.dataset],
                    "query": query,
                    "topK": max(1, min(limit, 20)),
                    "onlyContext": True,
                    "verbose": True,
                }
                response = await client.post(
                    f"{self.base}/api/v1/recall",
                    headers=self._headers(),
                    json=legacy_payload,
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
    """Live Bright Data search with verified-replay resilience.

    External content is untrusted. Only bounded search result fields become
    Evidence. Successful live searches are cached locally so a venue/network
    timeout can replay the last verified Bright Data result without pretending
    it is live.
    """

    def __init__(self) -> None:
        self.base = os.getenv("BRIGHTDATA_MCP_URL", "https://mcp.brightdata.com/mcp").rstrip("/")
        self.token = os.getenv("BRIGHTDATA_API_TOKEN", "")
        self.cache_path = Path(
            os.getenv(
                "BRIGHTDATA_REPLAY_CACHE",
                str(Path(__file__).resolve().parent / ".runtime" / "brightdata_last.json"),
            )
        )

    @staticmethod
    def _parse_sse(text: str) -> dict:
        payloads = []
        for line in text.splitlines():
            if line.startswith("data: "):
                try:
                    payloads.append(json.loads(line[6:]))
                except json.JSONDecodeError:
                    continue
        if payloads:
            return payloads[-1]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text[:4000]}

    @staticmethod
    def _extract_search_payload(text: str) -> dict:
        begin = text.find("_BEGIN=====")
        end = text.find("=====UNTRUSTED_", begin + 1) if begin >= 0 else -1
        candidate = text[begin + len("_BEGIN====="):end] if begin >= 0 and end > begin else text
        left = candidate.find("{")
        right = candidate.rfind("}")
        if left < 0 or right <= left:
            return {}
        try:
            return json.loads(candidate[left:right + 1])
        except json.JSONDecodeError:
            return {}

    def _to_evidence(self, organic: list[dict], limit: int, *, replay: bool) -> list[Evidence]:
        evidence: list[Evidence] = []
        for item in organic[: max(1, min(limit, 10))]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            description = str(item.get("description") or "").strip()
            link = str(item.get("link") or "").strip()
            prefix = "[VERIFIED REPLAY][UNTRUSTED WEB DATA]" if replay else "[UNTRUSTED WEB DATA]"
            evidence.append(
                Evidence(
                    source="brightdata",
                    summary=f"{prefix} {title}: {description}"[:1800],
                    metadata={
                        "live": not replay,
                        "verified_replay": replay,
                        "untrusted_external": True,
                        "title": title[:300],
                        "url": link[:1200],
                    },
                )
            )
        return evidence

    def _read_cache(self, limit: int) -> list[Evidence]:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            organic = payload.get("organic") or []
            return self._to_evidence(organic, limit, replay=True)
        except Exception:
            return []

    def _write_cache(self, organic: list[dict]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps({"provider": "brightdata", "organic": organic}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    async def search(self, query: str, limit: int = 5) -> list[Evidence]:
        if not self.token:
            return self._read_cache(limit)

        params = {"token": self.token}
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        timeout = httpx.Timeout(24.0, connect=10.0)
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                init = await client.post(
                    self.base,
                    params=params,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": "inneros-personal-brain", "version": "0.3"},
                        },
                    },
                )
                init.raise_for_status()
                session = init.headers.get("mcp-session-id", "")
                if session:
                    headers["mcp-session-id"] = session
                    await client.post(
                        self.base,
                        params=params,
                        headers=headers,
                        json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
                    )

                response = await client.post(
                    self.base,
                    params=params,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": "search_engine",
                            "arguments": {
                                "query": query[:500],
                                "engine": "google",
                                "geo_location": "us",
                            },
                        },
                    },
                )
                response.raise_for_status()
                rpc = self._parse_sse(response.text)

            result = (rpc.get("result") or {}) if isinstance(rpc, dict) else {}
            if result.get("isError"):
                return self._read_cache(limit)

            content = result.get("content") or []
            merged = "\n".join(
                str(item.get("text") or "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
            payload = self._extract_search_payload(merged)
            organic = payload.get("organic") or []
            if organic:
                self._write_cache(organic)
                return self._to_evidence(organic, limit, replay=False)
            return self._read_cache(limit)
        except (httpx.TimeoutException, httpx.HTTPError):
            return self._read_cache(limit)
