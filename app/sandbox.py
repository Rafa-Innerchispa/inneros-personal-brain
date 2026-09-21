from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any


def _find_sbx() -> str | None:
    configured = os.getenv("SBX_BIN", "").strip()
    if configured and Path(configured).is_file():
        return configured
    system = shutil.which("sbx")
    if system:
        return system
    local_root = Path(__file__).resolve().parent / ".runtime" / "docker-sbx" / "bin"
    matches = list(local_root.rglob("sbx")) if local_root.exists() else []
    return str(matches[0]) if matches else None


class DockerSandboxExecutor:
    """Bounded Docker Sandboxes executor."""

    def __init__(self, workspace: str | None = None) -> None:
        self.workspace = Path(workspace or os.getenv("BRAIN_WORKSPACE", ".")).resolve()
        self.sbx_bin = _find_sbx()

    def status(self) -> dict[str, Any]:
        return {
            "ok": bool(self.sbx_bin) and os.path.exists("/dev/kvm"),
            "binary_present": bool(self.sbx_bin),
            "binary": self.sbx_bin or "",
            "kvm": os.path.exists("/dev/kvm"),
            "enabled": os.getenv("DOCKER_SANDBOX_ENABLED", "0") == "1",
            "workspace": str(self.workspace),
        }

    def smoke(self) -> dict[str, Any]:
        state = self.status()
        if not state["binary_present"]:
            return {**state, "ok": False, "error": "sbx_not_installed"}
        if not state["kvm"]:
            return {**state, "ok": False, "error": "kvm_not_available"}

        auth = subprocess.run(
            [self.sbx_bin, "ls"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if auth.returncode != 0:
            return {
                **state,
                "ok": False,
                "error": "docker_auth_required"
                if "Not authenticated" in auth.stderr
                else "sbx_status_failed",
                "stderr": auth.stderr[-1000:],
            }
        if not state["enabled"]:
            return {**state, "ok": False, "error": "sandbox_not_enabled"}

        command = [
            self.sbx_bin,
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
            timeout=120,
            check=False,
        )
        return {
            **state,
            "ok": proc.returncode == 0 and "INNEROS_DOCKER_SANDBOX_OK" in proc.stdout,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-1000:],
            "stderr": proc.stderr[-1000:],
        }

    def prepare_artifact(self, prompt: str) -> dict[str, Any]:
        state = self.smoke()
        if not state.get("ok"):
            return {
                "ok": False,
                "status": "requires_runtime",
                "provider": "docker-sandboxes",
                "reason": state.get("error", "docker_sandbox_not_ready"),
                "runtime": {
                    "binary_present": state.get("binary_present"),
                    "kvm": state.get("kvm"),
                    "enabled": state.get("enabled"),
                },
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
            [self.sbx_bin, "run", "shell", str(self.workspace), "--", "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
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
