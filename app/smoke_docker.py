from __future__ import annotations

import json
import os
import shutil
import subprocess


def run(argv: list[str]) -> dict:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=30, check=False)
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-1000:],
            "stderr": p.stderr[-1000:],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    result = {
        "sbx_path": shutil.which("sbx"),
        "docker_path": shutil.which("docker"),
        "kvm_exists": os.path.exists("/dev/kvm"),
    }
    if result["docker_path"]:
        result["docker_version"] = run(["docker", "--version"])
    if result["sbx_path"]:
        result["sbx_version"] = run(["sbx", "--version"])

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
