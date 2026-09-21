from __future__ import annotations

import json
import urllib.request


def get(path: str):
    with urllib.request.urlopen("http://127.0.0.1:8230"+path,timeout=20) as r:
        return r.status,json.loads(r.read().decode())


def post(path: str,payload: dict):
    req=urllib.request.Request(
        "http://127.0.0.1:8230"+path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req,timeout=180) as r:
        return r.status,json.loads(r.read().decode())


def main() -> int:
    _,status=get("/api/status")
    _,body=post("/api/brain",{
        "prompt":"Find one current AI opportunity in San Francisco that matches a builder working on local-first AI agents, then prepare a safe action artifact.",
        "act":True,
    })
    action=(body.get("actions") or [{}])[0]
    out={
        "status":status,
        "memory_hits":len(body.get("memory_hits") or []),
        "web_hits":len(body.get("web_hits") or []),
        "trace":body.get("trace") or [],
        "action":action,
        "answer_preview":(body.get("answer") or "")[:1600],
    }
    print(json.dumps(out,indent=2))
    ok=(
        status.get("cognee",{}).get("state")=="ready"
        and status.get("brightdata",{}).get("state")=="ready"
        and status.get("strands",{}).get("state")=="ready"
        and status.get("docker",{}).get("state")=="ready"
        and out["memory_hits"]>=1
        and out["web_hits"]>=1
        and action.get("status")=="executed"
        and "remember:store-outcome" in out["trace"]
    )
    return 0 if ok else 2


if __name__=="__main__":
    raise SystemExit(main())
