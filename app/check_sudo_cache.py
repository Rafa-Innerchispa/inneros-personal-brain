from __future__ import annotations

import json
import subprocess


def main() -> int:
    p = subprocess.run(
        ["sudo", "-n", "true"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    print(json.dumps({
        "cached_admin_available": p.returncode == 0,
        "returncode": p.returncode,
        "stderr": (p.stderr or "")[-1000:],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
