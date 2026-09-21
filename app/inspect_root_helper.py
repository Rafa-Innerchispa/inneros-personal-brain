from __future__ import annotations

import json
import subprocess


def run(args: list[str]) -> dict:
    p = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
    return {
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[-6000:],
        "stderr": (p.stderr or "")[-6000:],
    }


def main() -> int:
    helper = "/usr/local/sbin/ralfia-peer-root-helper"
    out = {
        "help": run(["sudo", "-n", helper, "--help"]),
        "no_args": run(["sudo", "-n", helper]),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
