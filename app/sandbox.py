from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
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


def _find_docker() -> str | None:
    configured = os.getenv("DOCKER_BIN", "").strip()
    if configured and Path(configured).is_file():
        return configured
    return shutil.which("docker")


def _run_with_kvm(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    command = " ".join(shlex.quote(x) for x in argv)
    return subprocess.run(
        ["sg", "kvm", "-c", command],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _with_kvm_group(argv: list[str]) -> list[str]:
    """Run sbx with immediate kvm group membership when the current session is stale."""
    try:
        current = subprocess.run(
            ["id", "-nG"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        groups = set((current.stdout or "").split())
    except Exception:
        groups = set()
    if "kvm" in groups:
        return argv
    if shutil.which("sg"):
        return ["sg", "kvm", "-c", shlex.join(argv)]
    return argv


class DockerSandboxExecutor:
    """Bounded Docker Sandboxes executor with explicit KVM group context."""

    def __init__(self, workspace: str | None = None) -> None:
        self.workspace = Path(workspace or os.getenv("BRAIN_WORKSPACE", ".")).resolve()
        self.sbx_bin = _find_sbx()
        self.docker_bin = _find_docker()
        self.runtime_dir = Path(__file__).resolve().parent / ".runtime"
        self.smoke_cache = self.runtime_dir / "docker_smoke.json"

    def status(self) -> dict[str, Any]:
        return {
            "ok": bool(self.sbx_bin or self.docker_bin),
            "binary_present": bool(self.sbx_bin),
            "binary": self.sbx_bin or "",
            "docker_present": bool(self.docker_bin),
            "docker_binary": self.docker_bin or "",
            "kvm": os.path.exists("/dev/kvm"),
            "enabled": os.getenv("DOCKER_SANDBOX_ENABLED", "0") == "1",
            "workspace": str(self.workspace),
            "sandbox": SANDBOX_NAME,
        }

    def _cached_smoke(self) -> dict[str, Any] | None:
        try:
            payload = json.loads(self.smoke_cache.read_text(encoding="utf-8"))
            ttl = int(os.getenv("DOCKER_SMOKE_CACHE_SECONDS", "45"))
            if time.time() - float(payload.get("timestamp", 0)) <= ttl:
                return payload.get("result") if isinstance(payload.get("result"), dict) else None
        except Exception:
            return None
        return None

    def _write_smoke_cache(self, result: dict[str, Any]) -> None:
        try:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            self.smoke_cache.write_text(
                json.dumps({"timestamp": time.time(), "result": result}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _smoke_docker_cli(self, state: dict[str, Any]) -> dict[str, Any]:
        if not self.docker_bin:
            return {**state, "ok": False, "error": "docker_cli_not_installed"}
        probe = subprocess.run(
            [
                self.docker_bin,
                "run",
                "--rm",
                "python:3.12-slim",
                "python",
                "-c",
                "print('INNEROS_DOCKER_SANDBOX_OK')",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return {
            **state,
            "ok": probe.returncode == 0 and "INNEROS_DOCKER_SANDBOX_OK" in (probe.stdout or ""),
            "provider": "docker-cli",
            "returncode": probe.returncode,
            "stdout": (probe.stdout or "")[-1000:],
            "stderr": (probe.stderr or "")[-1000:],
            "error": "" if probe.returncode == 0 else "docker_cli_probe_failed",
        }

    def smoke(self) -> dict[str, Any]:
        cached = self._cached_smoke()
        if cached:
            return cached
        state = self.status()
        if not state["binary_present"]:
            result = self._smoke_docker_cli(state)
            self._write_smoke_cache(result)
            return result
        if not state["kvm"]:
            result = self._smoke_docker_cli(state)
            self._write_smoke_cache(result)
            return result

        diagnose = _run_with_kvm([self.sbx_bin, "diagnose", "--output", "json"], timeout=90)
        if diagnose.returncode != 0:
            detail = (diagnose.stdout or "") + (diagnose.stderr or "")
            if "not authenticated" in detail.lower():
                result = {**state, "ok": False, "error": "docker_auth_required"}
                self._write_smoke_cache(result)
                return result
            result = self._smoke_docker_cli({**state, "sbx_error": "sbx_diagnose_failed", "sbx_detail": detail[-1500:]})
            self._write_smoke_cache(result)
            return result

        if not state["enabled"]:
            result = self._smoke_docker_cli({**state, "sbx_error": "sandbox_not_enabled"})
            self._write_smoke_cache(result)
            return result

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

        result = {
            **state,
            "ok": probe.returncode == 0 and "INNEROS_DOCKER_SANDBOX_OK" in (probe.stdout or ""),
            "provider": "docker-sandboxes",
            "returncode": probe.returncode,
            "stdout": (probe.stdout or "")[-1000:],
            "stderr": (probe.stderr or "")[-1000:],
        }
        self._write_smoke_cache(result)
        return result

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
        if state.get("provider") == "docker-cli":
            proc = subprocess.run(
                [
                    self.docker_bin or "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{self.workspace}:/workspace",
                    "-w",
                    "/workspace",
                    "python:3.12-slim",
                    "python",
                    "-c",
                    python_code,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            return {
                "ok": proc.returncode == 0,
                "status": "executed" if proc.returncode == 0 else "failed",
                "provider": "docker-cli",
                "sandbox": "docker-run-python",
                "returncode": proc.returncode,
                "artifact": (proc.stdout or "").strip()[-500:],
                "stderr": (proc.stderr or "")[-1000:],
            }

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
