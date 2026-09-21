from __future__ import annotations

import json
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "app" / ".runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    out = runtime / "FINAL_E2E.log"
    result = runtime / "FINAL_E2E.json"
    result.unlink(missing_ok=True)
    fh = open(out, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(root / ".venv" / "bin" / "python"), "-u", str(root / "app" / "final_e2e_to_file.py")],
        cwd=str(root),
        stdout=fh,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(json.dumps({"ok": True, "pid": proc.pid, "result": str(result), "log": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
