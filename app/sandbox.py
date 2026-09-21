from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any


SANDBOX_NAME = "shell-inneros-personal-brain"


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


def _run_with_kvm(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    command = " ".join(shlex.quote(x) for x in argv)
    return subprocess.run(
        ["sg", "kvm", "-c", command],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


class DockerSandboxExecutor:
    """Bounded Docker Sandboxes executor with explicit KVM group context."""

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
            "sandbox": SANDBOX_NAME,
        }

    def smoke(self) -> dict[str, Any]:
        state = self.status()
        if not state["binary_present"]:
            return {**state, "ok": False, "error": "sbx_not_installed"}
        if not state["kvm"]:
            return {**state, "ok": False, "error": "kvm_not_available"}

        diagnose = _run_with_kvm([self.sbx_bin, "diagnose", "--output", "json"], timeout=90)
        if diagnose.returncode != 0:
            detail = (diagnose.stdout or "") + (diagnose.stderr or "")
            if "not authenticated" in detail.lower():
                return {**state, "ok": False, "error": "docker_auth_required"}
            return {**state, "ok": False, "error": "sbx_diagnose_failed", "detail": detail[-1500:]}

        if not state["enabled"]:
            return {**state, "ok": False, "error": "sandbox_not_enabled"}

        probe = _run_with_kvm(
            [self.sbx_bin, "exec", SANDBOX_NAME, "sh", "-lc", "printf 'INNEROS_DOCKER_SANDBOX_OK'"],
            timeout=120,
        )
        if probe.returncode != 0 and "not found" in ((probe.stderr or "") + (probe.stdout or "")).lower():
            create = _run_with_kvm(
                [self.sbx_bin, "run", "-d", "--name", SANDBOX_NAME, "shell", str(self.workspace)],
                timeout=180,
            )
            if create.returncode != 0:
                return {
                    **state,
                    "ok": False,
                    "error": "sandbox_create_failed",
                    "stderr": create.stderr[-1500:],
                    "stdout": create.stdout[-1500:],
                }
            probe = _run_with_kvm(
                [self.sbx_bin, "exec", SANDBOX_NAME, "sh", "-lc", "printf 'INNEROS_DOCKER_SANDBOX_OK'"],
                timeout=120,
            )

        return {
            **state,
            "ok": probe.returncode == 0 and "INNEROS_DOCKER_SANDBOX_OK" in (probe.stdout or ""),
            "returncode": probe.returncode,
            "stdout": (probe.stdout or "")[-1000:],
            "stderr": (probe.stderr or "")[-1000:],
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

        safe_prompt = prompt[:1600]
        payload = json.dumps({"request": safe_prompt}, ensure_ascii=False)
        python_code = (
            "import json, pathlib; "
            f"data=json.loads({payload!r}); "
            "p=pathlib.Path.cwd() / 'PERSONAL_BRAIN_ACTION.md'; "
            "p.write_text('# Personal Brain Action\\n\\n'+data['request']+'\\n', encoding='utf-8'); "
            "print(str(p))"
        )
        proc = _run_with_kvm(
            [self.sbx_bin, "exec", SANDBOX_NAME, "python3", "-c", python_code],
            timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "status": "executed" if proc.returncode == 0 else "failed",
            "provider": "docker-sandboxes",
            "sandbox": SANDBOX_NAME,
            "returncode": proc.returncode,
            "artifact": (proc.stdout or "").strip()[-500:],
            "stderr": (proc.stderr or "")[-1000:],
        }
