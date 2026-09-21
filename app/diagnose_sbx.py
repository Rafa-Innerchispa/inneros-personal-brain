from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def run(argv: list[str], timeout: int = 90) -> dict:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-12000:],
            "stderr": p.stderr[-12000:],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    root = Path(__file__).resolve().parent / ".runtime" / "docker-sbx" / "bin"
    matches = list(root.rglob("sbx"))
    if not matches:
        print(json.dumps({"ok": False, "error": "sbx_not_found"}))
        return 2
    sbx = str(matches[0])
    result = {
        "diagnose": run([sbx, "diagnose", "--output", "json"], 120),
        "id": run(["id"]),
        "kvm": {
            "exists": os.path.exists("/dev/kvm"),
            "stat": run(["stat", "-c", "%A %U %G %a", "/dev/kvm"]) if os.path.exists("/dev/kvm") else None,
        },
        "lsmod_kvm": run(["lsmod"]),
    }
    if result["lsmod_kvm"].get("stdout"):
        result["lsmod_kvm"]["stdout"] = "\n".join(
            line for line in result["lsmod_kvm"]["stdout"].splitlines()
            if "kvm" in line.lower()
        )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
