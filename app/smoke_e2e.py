from __future__ import annotations

import json
import urllib.request


def main() -> int:
    payload = json.dumps({
        "prompt": "What marker proves that Cognee persistent memory is working for InnerOS Personal Brain?",
        "act": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8230/api/brain",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        body = json.loads(r.read().decode("utf-8"))
    out = {
        "answer": body.get("answer", "")[:1200],
        "memory_hits": len(body.get("memory_hits") or []),
        "web_hits": len(body.get("web_hits") or []),
        "trace": body.get("trace") or [],
        "marker_in_memory": any(
            "INNEROS_COGNEE_MEMORY_OK_20260921" in str(item)
            for item in body.get("memory_hits") or []
        ),
    }
    print(json.dumps(out, indent=2))
    return 0 if out["memory_hits"] and out["marker_in_memory"] and "remember:store-outcome" in out["trace"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
