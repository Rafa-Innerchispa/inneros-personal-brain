from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.memory_fabric import build_memory_fabric


def main() -> None:
    fabric = build_memory_fabric().as_dict()
    print(json.dumps(fabric, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
