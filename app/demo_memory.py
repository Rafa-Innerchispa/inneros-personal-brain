from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "demo_memory_seed.json"
RUNTIME_DIR = ROOT / ".runtime"
MARKER_FILE = RUNTIME_DIR / "real_memory_seed.ok"
MARKER = "INNEROS_REAL_MEMORY_SEED_20260921_V1"


def seed_status() -> dict:
    return {
        "marker": MARKER,
        "seeded": MARKER_FILE.exists(),
        "state": "ready" if MARKER_FILE.exists() else "pending",
    }


async def ensure_real_memory_seed() -> dict:
    if MARKER_FILE.exists():
        return {"ok": True, "already_seeded": True, **seed_status()}

    base = os.getenv("COGNEE_SERVICE_URL", "").rstrip("/")
    key = os.getenv("COGNEE_API_KEY", "")
    dataset = os.getenv("COGNEE_DATASET", "inneros-personal-brain")
    if not base or not key or not SEED_FILE.exists():
        return {"ok": False, "error": "cognee_seed_runtime_not_ready", **seed_status()}

    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    headers = {"X-Api-Key": key}

    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        # Idempotency check: query the unique marker before writing.
        try:
            recall = await client.post(
                base + "/api/v1/recall",
                headers=headers,
                json={
                    "searchType": None,
                    "datasets": [dataset],
                    "query": MARKER,
                    "topK": 6,
                    "onlyContext": True,
                    "verbose": True,
                },
            )
            if recall.is_success and MARKER in recall.text:
                RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
                MARKER_FILE.write_text(
                    json.dumps({"marker": MARKER, "source": "existing-cognee-memory"}),
                    encoding="utf-8",
                )
                return {"ok": True, "already_seeded": True, **seed_status()}
        except httpx.HTTPError:
            pass

        document = [
            MARKER,
            "Curated real project memory for the InnerOS Personal Brain.",
            "Operational project facts only. Credentials and sensitive personal information are intentionally excluded.",
            "",
        ]
        for fact in seed.get("facts", []):
            document.extend([f"## {fact['topic']}", fact["text"], ""])

        remember = await client.post(
            base + "/api/v1/remember",
            headers=headers,
            files=[
                ("raw_data", (None, "\n".join(document))),
                ("datasetName", (None, dataset)),
                ("run_in_background", (None, "false")),
                ("node_set", (None, "inneros-real-memory")),
            ],
            timeout=240,
        )
        remember.raise_for_status()

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    MARKER_FILE.write_text(
        json.dumps(
            {
                "marker": MARKER,
                "seed_version": seed.get("seed_version"),
                "facts_loaded": len(seed.get("facts", [])),
            }
        ),
        encoding="utf-8",
    )
    return {"ok": True, "already_seeded": False, **seed_status()}


async def seed_in_background() -> None:
    try:
        await ensure_real_memory_seed()
    except Exception:
        # Seeding must never prevent the brain from starting.
        return
