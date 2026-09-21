from __future__ import annotations

import json
import subprocess


def run(argv: list[str]) -> dict:
    p = subprocess.run(argv, capture_output=True, text=True, timeout=20, check=False)
    return {
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[-4000:],
        "stderr": (p.stderr or "")[-4000:],
    }


def main() -> int:
    out = {
        "group_entry": run(["getent", "group", "kvm"]),
        "current_id": run(["id"]),
        "sg_id": run(["sg", "kvm", "-c", "id"]),
        "sg_kvm_test": run(["sg", "kvm", "-c", "test -r /dev/kvm -a -w /dev/kvm && echo KVM_OK"]),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
