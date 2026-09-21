from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path


def main() -> int:
    runtime = Path(__file__).resolve().parent / ".runtime"
    root = runtime / "docker-sbx" / "bin"
    matches = list(root.rglob("sbx"))
    if not matches:
        print(json.dumps({"ok": False, "error": "sbx_not_found"}))
        return 2

    runtime.mkdir(parents=True, exist_ok=True)
    log = runtime / "sbx-login.log"
    pid_file = runtime / "sbx-login.pid"

    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            os.kill(old_pid, 0)
            print(json.dumps({"ok": True, "already_running": True, "pid": old_pid, "log": str(log)}))
            return 0
        except Exception:
            pid_file.unlink(missing_ok=True)

    out = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(matches[0]), "login"],
        stdin=subprocess.DEVNULL,
        stdout=out,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    pid_file.write_text(str(proc.pid), encoding="utf-8")
    time.sleep(2)
    text = log.read_text(encoding="utf-8") if log.exists() else ""
    print(json.dumps({
        "ok": True,
        "pid": proc.pid,
        "log": str(log),
        "output": text[-3000:],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
