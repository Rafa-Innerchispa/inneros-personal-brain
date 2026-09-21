from __future__ import annotations

import json
import urllib.request
from pathlib import Path


OUT = Path(__file__).resolve().parent / ".runtime" / "FINAL_E2E.json"


def main() -> int:
    payload = json.dumps({
        "prompt": "Use my persistent memory and live web context to identify one relevant AI opportunity and prepare a safe action artifact.",
        "act": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8230/api/brain",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        body = json.loads(r.read().decode("utf-8"))

    with urllib.request.urlopen("http://127.0.0.1:8230/api/status", timeout=30) as r:
        sponsors = json.loads(r.read().decode("utf-8"))

    actions = body.get("actions") or []
    result = {
        "ok": True,
        "answer_preview": (body.get("answer") or "")[:1600],
        "memory_hits": len(body.get("memory_hits") or []),
        "web_hits": len(body.get("web_hits") or []),
        "trace": body.get("trace") or [],
        "actions": actions,
        "sponsors": sponsors,
        "docker_executed": any(
            isinstance(a, dict) and a.get("ok") and a.get("status") == "executed"
            for a in actions
        ),
    }
    result["all_four_green"] = all(
        sponsors.get(name, {}).get("state") == "ready"
        for name in ("cognee", "brightdata", "strands", "docker")
    )
    result["ok"] = (
        result["memory_hits"] > 0
        and result["web_hits"] > 0
        and result["docker_executed"]
        and result["all_four_green"]
        and "remember:store-outcome" in result["trace"]
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
