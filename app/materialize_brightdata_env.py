from __future__ import annotations

import json
import subprocess


def main() -> int:
    py = "/home/rlopez/inneros/inneros_core/platform/venv/bin/python3"
    code = r'''
import json
from inneros_core_runtime.owner_vault_bridge import materialize_project_env
result = materialize_project_env(
    namespace="inneros-personal-brain",
    bindings={"BRIGHTDATA_API_TOKEN": "owner_vault:brightdata/api_token"},
    static_values={"BRIGHTDATA_MCP_URL": "https://mcp.brightdata.com/mcp"},
    actor="RAFAEL",
)
print(json.dumps(result))
'''
    p = subprocess.run(
        [py, "-c", code],
        cwd="/home/rlopez/inneros/inneros_core/platform",
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={
            "PYTHONPATH": "/home/rlopez/inneros/inneros_core/platform",
            "HOME": "/home/rlopez",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        },
    )
    payload = {}
    try:
        payload = json.loads((p.stdout or "").strip() or "{}")
    except Exception:
        payload = {"ok": False, "error": "invalid_bridge_response"}
    safe = {
        "ok": bool(payload.get("ok")) and p.returncode == 0,
        "path": payload.get("path"),
        "namespace": payload.get("namespace"),
        "materialized_env_keys": payload.get("materialized_env_keys"),
        "static_env_keys": payload.get("static_env_keys"),
        "secret_returned": payload.get("secret_returned"),
        "returncode": p.returncode,
        "stderr": (p.stderr or "")[-1000:],
    }
    print(json.dumps(safe, indent=2))
    return 0 if safe["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
