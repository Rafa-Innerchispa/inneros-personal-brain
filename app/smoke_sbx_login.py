from __future__ import annotations

import json
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent / ".runtime" / "docker-sbx" / "bin"
    matches = list(root.rglob("sbx"))
    if not matches:
        print(json.dumps({"ok": False, "error": "sbx_not_found"}))
        return 2
    sbx = str(matches[0])
    try:
        p = subprocess.run(
            [sbx, "login"],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        print(json.dumps({
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
        }, indent=2))
        return 0
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        print(json.dumps({
            "ok": False,
            "timed_out": True,
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
        }, indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
