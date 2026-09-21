from __future__ import annotations

import json
import urllib.request


def get(path: str):
    with urllib.request.urlopen("http://127.0.0.1:8230" + path, timeout=15) as r:
        return r.status, r.read().decode("utf-8")


def main() -> int:
    health_status, health = get("/health")
    status_status, status = get("/api/status")
    root_status, root = get("/")
    payload = {
        "health_status": health_status,
        "health": json.loads(health),
        "status_status": status_status,
        "sponsors": json.loads(status),
        "root_status": root_status,
        "ui_marker": "InnerOS Personal Brain" in root,
    }
    print(json.dumps(payload, indent=2))
    return 0 if health_status == 200 and status_status == 200 and root_status == 200 and payload["ui_marker"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
