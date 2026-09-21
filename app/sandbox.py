from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any


class DockerSandboxExecutor:
    """Bounded Docker Sandboxes executor.

    It never shells through an untrusted string. Commands are passed as argv,
    and execution is disabled unless DOCKER_SANDBOX_ENABLED=1.
    """

    def __init__(self, workspace: str | None = None) -> None:
        self.workspace = Path(workspace or os.getenv("BRAIN_WORKSPACE", ".")).resolve()

    def status(self) -> dict[str, Any]:
        binary = shutil.which("sbx")
        return {
            "ok": bool(binary),
            "binary_present": bool(binary),
            "binary": binary or "",
            "enabled": os.getenv("DOCKER_SANDBOX_ENABLED", "0") == "1",
            "workspace": str(self.workspace),
        }

    def smoke(self) -> dict[str, Any]:
        state = self.status()
        if not state["binary_present"]:
            return {**state, "ok": False, "error": "sbx_not_installed"}
        if not state["enabled"]:
            return {**state, "ok": False, "error": "sandbox_not_enabled"}

        name = f"inneros-brain-{uuid.uuid4().hex[:8]}"
        command = [
            "sbx",
            "run",
            "shell",
            str(self.workspace),
            "--",
            "-c",
            "printf 'INNEROS_DOCKER_SANDBOX_OK'",
        ]
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        return {
            **state,
            "ok": proc.returncode == 0 and "INNEROS_DOCKER_SANDBOX_OK" in proc.stdout,
            "sandbox_name": name,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-1000:],
            "stderr": proc.stderr[-1000:],
        }

    def prepare_artifact(self, prompt: str) -> dict[str, Any]:
        """Prepare a bounded demo artifact inside a sandbox."""
        state = self.status()
        if not state["binary_present"] or not state["enabled"]:
            return {
                "ok": False,
                "status": "requires_runtime",
                "reason": state.get("error") or "docker_sandbox_not_ready",
            }

        safe_prompt = prompt[:1200]
        payload = json.dumps({"request": safe_prompt}, ensure_ascii=False)
        script = (
            "python3 -c "
            + repr(
                "import json, pathlib; "
                f"data=json.loads({payload!r}); "
                "p=pathlib.Path('PERSONAL_BRAIN_ACTION.md'); "
                "p.write_text('# Personal Brain Action\\n\\n'+data['request']+'\\n', encoding='utf-8'); "
                "print(str(p))"
            )
        )
        proc = subprocess.run(
            ["sbx", "run", "shell", str(self.workspace), "--", "-c", script],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "status": "executed" if proc.returncode == 0 else "failed",
            "provider": "docker-sandboxes",
            "returncode": proc.returncode,
            "artifact": proc.stdout.strip()[-500:],
            "stderr": proc.stderr[-1000:],
        }
