from __future__ import annotations

import json
import urllib.request


def post(path: str, payload: dict, timeout: int = 180):
    req = urllib.request.Request(
        "http://127.0.0.1:8230" + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def get(path: str, timeout: int = 30):
    with urllib.request.urlopen("http://127.0.0.1:8230" + path, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def main() -> int:
    status_code, sponsors = get("/api/status")
    brain_code, body = post("/api/brain", {
        "prompt": "Using my persistent memory and live web context, tell me one AI opportunity in San Francisco relevant to InnerOS and prepare a safe action artifact.",
        "act": True,
    })
    out = {
        "status_code": status_code,
        "sponsors": sponsors,
        "brain_code": brain_code,
        "answer_preview": (body.get("answer") or "")[:1800],
        "memory_hits": len(body.get("memory_hits") or []),
        "web_hits": len(body.get("web_hits") or []),
        "actions": body.get("actions") or [],
        "trace": body.get("trace") or [],
    }
    out["docker_executed"] = any(a.get("status") == "executed" and a.get("ok") for a in out["actions"] if isinstance(a, dict))
    out["all_green"] = (
        sponsors.get("cognee", {}).get("state") == "ready"
        and sponsors.get("brightdata", {}).get("state") == "ready"
        and sponsors.get("strands", {}).get("state") == "ready"
        and sponsors.get("docker", {}).get("state") == "ready"
    )
    print(json.dumps(out, indent=2)[:20000])
    return 0 if brain_code == 200 and out["web_hits"] > 0 and out["memory_hits"] > 0 and out["docker_executed"] and out["all_green"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
