from __future__ import annotations

import json
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    runtime = root / "app" / ".runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    out = runtime / "full-stack-smoke.log"
    done = runtime / "full-stack-smoke.done"
    done.unlink(missing_ok=True)
    fh = open(out, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(root / ".venv" / "bin" / "python"), str(root / "app" / "smoke_full_stack.py")],
        cwd=str(root),
        stdout=fh,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    (runtime / "full-stack-smoke.pid").write_text(str(proc.pid), encoding="utf-8")
    print(json.dumps({"ok": True, "pid": proc.pid, "log": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
