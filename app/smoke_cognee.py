from __future__ import annotations

import json
from pathlib import Path

import httpx


def load_env() -> dict[str, str]:
    path = Path(__file__).resolve().parent / ".runtime" / "cognee.env"
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    env = load_env()
    base = env["COGNEE_SERVICE_URL"].rstrip("/")
    key = env["COGNEE_API_KEY"]
    headers = {"X-Api-Key": key}
    out: dict = {"base_configured": True, "credential_present": bool(key)}

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for path in ["/health", "/api/v1/health", "/openapi.json"]:
            try:
                r = client.get(base + path, headers=headers)
                out[path] = {
                    "status": r.status_code,
                    "content_type": r.headers.get("content-type", ""),
                    "preview": r.text[:300] if path != "/openapi.json" else "",
                }
                if path == "/openapi.json" and r.status_code == 200:
                    spec = r.json()
                    paths = list((spec.get("paths") or {}).keys())
                    out["memory_paths"] = [
                        p for p in paths
                        if any(k in p.lower() for k in ("remember", "recall", "search", "memory"))
                    ][:50]
            except Exception as exc:
                out[path] = {"error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
