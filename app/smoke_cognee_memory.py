from __future__ import annotations

import json
import time
from pathlib import Path

import httpx


MARKER = "INNEROS_COGNEE_MEMORY_OK_20260921"


def load_env() -> dict[str, str]:
    p = Path(__file__).resolve().parent / ".runtime" / "cognee.env"
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def main() -> int:
    e = load_env()
    base = e["COGNEE_SERVICE_URL"].rstrip("/")
    dataset = e.get("COGNEE_DATASET", "inneros-personal-brain")
    key = e["COGNEE_API_KEY"]
    headers = {"X-Api-Key": key, "Authorization": f"Bearer {key}"}

    memory = (
        f"{MARKER}. InnerOS Personal Brain uses Cognee for persistent structured memory. "
        "This memory was written during the Battle of the Personal Brains hackathon integration smoke."
    )

    with httpx.Client(timeout=240, follow_redirects=True) as client:
        files = [
            ("raw_data", (None, memory)),
            ("datasetName", (None, dataset)),
            ("run_in_background", (None, "false")),
            ("node_set", (None, "personal-brain-demo")),
        ]
        remember = client.post(base + "/api/v1/remember", headers=headers, files=files)
        remember_preview = remember.text[:2000]

        result = {
            "remember_status": remember.status_code,
            "remember_ok": remember.is_success,
            "remember_preview": remember_preview,
            "dataset": dataset,
        }

        if not remember.is_success:
            print(json.dumps(result, indent=2))
            return 2

        recall_payload = {
            "searchType": None,
            "datasets": [dataset],
            "query": "What marker proves the InnerOS Personal Brain Cognee memory smoke?",
            "topK": 10,
            "onlyContext": True,
            "verbose": True,
        }
        recall = client.post(base + "/api/v1/recall", headers=headers, json=recall_payload)
        text = recall.text
        result.update({
            "recall_status": recall.status_code,
            "recall_ok": recall.is_success,
            "marker_found": MARKER in text,
            "recall_preview": text[:3000],
        })

    print(json.dumps(result, indent=2))
    return 0 if result["recall_ok"] and result["marker_found"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
