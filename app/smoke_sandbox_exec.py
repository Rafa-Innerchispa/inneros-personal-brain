from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sbx = str(list((root / "app" / ".runtime" / "docker-sbx" / "bin").rglob("sbx"))[0])
    sandbox = "shell-inneros-personal-brain"
    cmd = (
        f"{shlex.quote(sbx)} exec {shlex.quote(sandbox)} "
        "sh -lc " + shlex.quote("printf 'INNEROS_DOCKER_SANDBOX_OK'")
    )
    p = subprocess.run(
        ["sg", "kvm", "-c", cmd],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    out = {
        "ok": p.returncode == 0 and "INNEROS_DOCKER_SANDBOX_OK" in (p.stdout or ""),
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[-4000:],
        "stderr": (p.stderr or "")[-4000:],
    }
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
