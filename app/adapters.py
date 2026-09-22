from __future__ import annotations

import json
import os
import re
from html import unescape
from urllib.parse import quote_plus
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
        try:
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
        except (httpx.HTTPError, ValueError) as exc:
            return [
                Evidence(
                    source="cognee",
                    summary="Cognee recall was temporarily unavailable; continuing with other live sources.",
                    metadata={
                        "dataset": self.dataset,
                        "live": False,
                        "unavailable": True,
                        "error_type": type(exc).__name__,
                    },
                )
            ]
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
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base}/api/v1/remember",
                    headers=self._headers(),
                    files=files,
                )
                response.raise_for_status()
        except (httpx.HTTPError, ValueError):
            return


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
        self.rest_api_key = os.getenv("BRIGHTDATA_API_KEY", "")
        self.rest_zone = os.getenv("BRIGHTDATA_SERP_ZONE", os.getenv("BRIGHTDATA_ZONE", "inneros"))
        self.rest_endpoint = os.getenv("BRIGHTDATA_REST_URL", "https://api.brightdata.com/request")
        self.cache_path = Path(
            os.getenv(
                "BRIGHTDATA_REPLAY_CACHE",
                str(Path(__file__).resolve().parent / ".runtime" / "brightdata_last.json"),
            )
        )

    @staticmethod
    def _normalize_query(query: str) -> str:
        return " ".join(query.lower().split())[:500]

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

    def _read_cache(self, query: str, limit: int) -> list[Evidence]:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if payload.get("query") != self._normalize_query(query):
                return []
            organic = payload.get("organic") or []
            return self._to_evidence(organic, limit, replay=True)
        except Exception:
            return []

    def _write_cache(self, query: str, organic: list[dict]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(
                    {
                        "provider": "brightdata",
                        "query": self._normalize_query(query),
                        "organic": organic,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    @staticmethod
    def _extract_rest_organic(payload: object) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        body = payload.get("body")
        if isinstance(body, str) and body.strip():
            try:
                parsed_body = json.loads(body)
                body_results = BrightDataAdapter._extract_rest_organic(parsed_body)
                if body_results:
                    return body_results
            except json.JSONDecodeError:
                body_results = BrightDataAdapter._extract_google_html_organic(body)
                if body_results:
                    return body_results
        candidates = [
            payload.get("organic"),
            payload.get("organic_results"),
            payload.get("results"),
            payload.get("search_results"),
        ]
        parsed = payload.get("parsed")
        if isinstance(parsed, dict):
            candidates.extend([
                parsed.get("organic"),
                parsed.get("organic_results"),
                parsed.get("results"),
                parsed.get("search_results"),
            ])
        for candidate in candidates:
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]
        return []

    @staticmethod
    def _strip_html(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value)
        return re.sub(r"\s+", " ", unescape(text)).strip()

    @staticmethod
    def _extract_google_html_organic(html: str) -> list[dict]:
        results: list[dict] = []
        patterns = [
            re.compile(
                r'<a[^>]+href="(?P<link>https?://[^"#]+)"[^>]*>.*?<h3[^>]*>(?P<title>.*?)</h3>',
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r'"title"\s*:\s*"(?P<title>[^"]{4,220})".{0,600}?"(?:link|url)"\s*:\s*"(?P<link>https?://[^"]+)"',
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r'"(?:link|url)"\s*:\s*"(?P<link>https?://[^"]+)".{0,600}?"title"\s*:\s*"(?P<title>[^"]{4,220})"',
                re.IGNORECASE | re.DOTALL,
            ),
        ]
        seen: set[str] = set()
        for pattern in patterns:
            for match in pattern.finditer(html):
                link = unescape(match.group("link")).replace("\\/", "/")
                title = BrightDataAdapter._strip_html(match.group("title").replace("\\/", "/"))
                if not title or link in seen:
                    continue
                if any(blocked in link for blocked in ("google.com/search", "webcache", "accounts.google")):
                    continue
                seen.add(link)
                results.append({"title": title, "description": "", "link": link})
                if len(results) >= 10:
                    return results
        return results

    @staticmethod
    def _brightdata_response_evidence(payload: dict, query: str) -> list[dict]:
        headers = payload.get("headers") if isinstance(payload.get("headers"), dict) else {}
        status_code = payload.get("status_code")
        warning = headers.get("x-brd-warning") or ""
        if status_code:
            return [{
                "title": "Bright Data SERP response received",
                "description": (
                    f"Bright Data returned HTTP {status_code} for the live query. "
                    f"{warning}".strip()
                ),
                "link": f"brightdata://serp/{quote_plus(query[:120])}",
            }]
        return []

    async def _search_rest_serp(self, query: str, limit: int) -> list[Evidence]:
        if not self.rest_api_key or not self.rest_zone:
            return []
        headers = {
            "Authorization": f"Bearer {self.rest_api_key}",
            "Content-Type": "application/json",
        }
        search_url = f"https://www.google.com/search?q={quote_plus(query[:500])}"
        parsed_payload = {
            "zone": self.rest_zone,
            "url": search_url,
            "format": "json",
            "data_format": "parsed",
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(35.0, connect=12.0)) as client:
            response = await client.post(self.rest_endpoint, headers=headers, json=parsed_payload)
            response.raise_for_status()
            data = response.json()
        organic = self._extract_rest_organic(data)
        if not organic:
            raw_payload = {
                "zone": self.rest_zone,
                "url": search_url,
                "format": "raw",
            }
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=12.0)) as client:
                response = await client.post(self.rest_endpoint, headers=headers, json=raw_payload)
                response.raise_for_status()
                data = response.json()
        organic = self._extract_rest_organic(data)
        if organic:
            self._write_cache(query, organic)
            return self._to_evidence(organic, limit, replay=False)
        if isinstance(data, dict):
            evidence_only = self._brightdata_response_evidence(data, query)
            if evidence_only:
                return self._to_evidence(evidence_only, limit, replay=False)
        return []

    async def search(self, query: str, limit: int = 5) -> list[Evidence]:
        try:
            rest_results = await self._search_rest_serp(query, limit)
            if rest_results:
                return rest_results
        except (httpx.TimeoutException, httpx.HTTPError, ValueError):
            pass

        if not self.token:
            return self._read_cache(query, limit)

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
                return self._read_cache(query, limit)

            content = result.get("content") or []
            merged = "\n".join(
                str(item.get("text") or "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
            payload = self._extract_search_payload(merged)
            organic = payload.get("organic") or []
            if organic:
                self._write_cache(query, organic)
                return self._to_evidence(organic, limit, replay=False)
            return self._read_cache(query, limit)
        except (httpx.TimeoutException, httpx.HTTPError):
            return self._read_cache(query, limit)
