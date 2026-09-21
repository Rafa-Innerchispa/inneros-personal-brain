from __future__ import annotations

from pathlib import Path


def main() -> int:
    p = Path("/usr/local/sbin/ralfia-peer-root-helper")
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"READ_ERROR:{type(exc).__name__}:{exc}")
        return 0
    for term in ("kvm", "group", "usermod", "gpasswd", "apt-install", "wifi-connect"):
        idx = text.lower().find(term.lower())
        print(f"TERM={term} IDX={idx}")
        if idx >= 0:
            print(text[max(0, idx-1200):idx+2600])
            print("---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
