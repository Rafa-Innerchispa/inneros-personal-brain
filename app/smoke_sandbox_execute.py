from __future__ import annotations

import json
import os

from app.sandbox import DockerSandboxExecutor


def main() -> int:
    os.environ["DOCKER_SANDBOX_ENABLED"] = "1"
    result = DockerSandboxExecutor().smoke()
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
