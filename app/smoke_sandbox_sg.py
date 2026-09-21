from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sbx_matches = list((root / "app" / ".runtime" / "docker-sbx" / "bin").rglob("sbx"))
    if not sbx_matches:
        print(json.dumps({"ok": False, "error": "sbx_not_found"}))
        return 2
    sbx = str(sbx_matches[0])

    def run(cmd: str, timeout: int = 120):
        p = subprocess.run(
            ["sg", "kvm", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": (p.stdout or "")[-4000:],
            "stderr": (p.stderr or "")[-4000:],
        }

    group_check = run("id")
    daemon = run(f"{shlex.quote(sbx)} daemon start", 60)
    diagnose = run(f"{shlex.quote(sbx)} diagnose --output json", 90)
    sandbox = run(
        f"{shlex.quote(sbx)} run shell {shlex.quote(str(root))} -- -c "
        + shlex.quote("printf 'INNEROS_DOCKER_SANDBOX_OK'"),
        180,
    )

    result = {
        "group_check": group_check,
        "daemon_start": daemon,
        "diagnose": diagnose,
        "sandbox": sandbox,
        "marker_found": "INNEROS_DOCKER_SANDBOX_OK" in sandbox.get("stdout", ""),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["marker_found"] and sandbox["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
