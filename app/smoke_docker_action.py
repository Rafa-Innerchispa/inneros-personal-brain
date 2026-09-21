from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.sandbox import DockerSandboxExecutor


def main() -> int:
    os.environ["DOCKER_SANDBOX_ENABLED"] = "1"
    result = DockerSandboxExecutor(workspace=str(ROOT)).prepare_artifact(
        "Create a verified action artifact for the InnerOS Personal Brain Docker sponsor smoke."
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") and result.get("status") == "executed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
