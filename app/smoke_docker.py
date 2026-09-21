from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def run(argv: list[str], timeout: int = 30) -> dict:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-2000:],
            "stderr": p.stderr[-2000:],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def find_sbx() -> str | None:
    direct = shutil.which("sbx")
    if direct:
        return direct
    local = Path(__file__).resolve().parent / ".runtime" / "docker-sbx" / "bin"
    matches = list(local.rglob("sbx")) if local.exists() else []
    return str(matches[0]) if matches else None


def main() -> int:
    sbx = find_sbx()
    result = {
        "sbx_path": sbx,
        "docker_path": shutil.which("docker"),
        "kvm_exists": os.path.exists("/dev/kvm"),
    }
    if result["docker_path"]:
        result["docker_version"] = run(["docker", "--version"])
    if sbx:
        result["sbx_version"] = run([sbx, "version"])
        result["sbx_list"] = run([sbx, "ls"], timeout=15)

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
