from __future__ import annotations

import json
from pathlib import Path

import httpx


def env():
    p = Path(__file__).resolve().parent / ".runtime" / "cognee.env"
    out = {}
    for line in p.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def main():
    e = env()
    headers = {"X-Api-Key": e["COGNEE_API_KEY"], "Authorization": f"Bearer {e['COGNEE_API_KEY']}"}
    spec = httpx.get(e["COGNEE_SERVICE_URL"].rstrip("/") + "/openapi.json", headers=headers, timeout=30).json()
    paths = spec.get("paths", {})
    selected = {}
    for p in ["/api/v1/remember", "/api/v1/recall", "/api/v1/search"]:
        selected[p] = paths.get(p, {})
    refs = {}
    for name, schema in (spec.get("components", {}).get("schemas", {}) or {}).items():
        if any(k in name.lower() for k in ("remember", "recall", "search")):
            refs[name] = schema
    print(json.dumps({"paths": selected, "schemas": refs}, indent=2)[:20000])


if __name__ == "__main__":
    main()
