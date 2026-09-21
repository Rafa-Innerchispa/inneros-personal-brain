from __future__ import annotations

import json
import subprocess


def main() -> int:
    p = subprocess.run(
        ["sudo", "-n", "-l"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    print(json.dumps({
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[-12000:],
        "stderr": (p.stderr or "")[-12000:],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
