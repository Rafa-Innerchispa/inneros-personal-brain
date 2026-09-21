from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "demo_memory_seed.json"
MARKER = "INNEROS_REAL_MEMORY_SEED_20260921_V1"


def load_runtime_env() -> None:
    paths = [
        ROOT / ".runtime" / "cognee.env",
        Path("/home/rlopez/.config/inneros-personal-brain/runtime.env"),
    ]
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def main() -> int:
    load_runtime_env()
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    base = os.environ["COGNEE_SERVICE_URL"].rstrip("/")
    key = os.environ["COGNEE_API_KEY"]
    dataset = os.environ.get("COGNEE_DATASET", seed["dataset"])

    document = [
        MARKER,
        "This is curated real project memory for the InnerOS Personal Brain demo.",
        "It contains operational facts only and intentionally excludes credentials and sensitive personal information.",
        "",
    ]
    for fact in seed["facts"]:
        document.append(f"## {fact['topic']}")
        document.append(fact["text"])
        document.append("")
    text = "\n".join(document)

    headers = {"X-Api-Key": key}
    files = [
        ("raw_data", (None, text)),
        ("datasetName", (None, dataset)),
        ("run_in_background", (None, "false")),
        ("node_set", (None, "inneros-real-memory")),
    ]

    with httpx.Client(timeout=240, follow_redirects=True) as client:
        remember = client.post(base + "/api/v1/remember", headers=headers, files=files)
        remember.raise_for_status()

        recall = client.post(
            base + "/api/v1/recall",
            headers=headers,
            json={
                "searchType": None,
                "datasets": [dataset],
                "query": "What real projects and architecture does this Personal Brain remember?",
                "topK": 12,
                "onlyContext": True,
                "verbose": True,
            },
        )
        recall.raise_for_status()
        rows = recall.json()
        serialized = json.dumps(rows, ensure_ascii=False, default=str)

    result = {
        "ok": bool(rows),
        "dataset": dataset,
        "seed_version": seed["seed_version"],
        "facts_loaded": len(seed["facts"]),
        "recall_count": len(rows) if isinstance(rows, list) else 1,
        "marker_found": MARKER in serialized,
        "sample": serialized[:4000],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
