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
    proc = subprocess.run(
        [sbx, "policy", "init", "balanced"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    print(json.dumps({
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-3000:],
        "stderr": proc.stderr[-3000:],
    }, indent=2))
    return 0 if proc.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
