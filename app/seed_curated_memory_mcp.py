from __future__ import annotations

import json
from pathlib import Path
import httpx

MCP_URL = "http://127.0.0.1:8241/mcp"
ROOT = Path(__file__).resolve().parent
SEED_FILE = ROOT / "demo_memory_seed.json"
RUNTIME_DIR = ROOT / ".runtime"


def parse_sse(text: str) -> dict:
    payloads = []
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                payloads.append(json.loads(line[6:]))
            except Exception:
                pass
    if payloads:
        return payloads[-1]
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text[:4000]}


def mcp_call(client: httpx.Client, headers: dict, request_id: int, tool: str, arguments: dict) -> dict:
    response = client.post(
        MCP_URL,
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        },
    )
    response.raise_for_status()
    return parse_sse(response.text)


def main() -> int:
    seed = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    dataset = seed["dataset"]
    seed_version = seed["seed_version"]
    marker_file = RUNTIME_DIR / f"curated_memory_{seed_version}.ok"

    document = [
        f"INNEROS_CURATED_MEMORY_SEED::{seed_version}",
        "Curated durable shared memory for InnerOS Personal Brain.",
        "This memory intentionally excludes credentials, tokens, private IP topology, private customer records, private email content, sensitive personal data and private pricing.",
        "",
    ]
    for fact in seed.get("facts", []):
        document.extend([f"## {fact['topic']}", fact["text"], ""])
    data = "\n".join(document)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    with httpx.Client(timeout=300) as client:
        init = client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "inneros-curated-memory-seeder", "version": "2"},
                },
            },
        )
        init.raise_for_status()
        session = init.headers.get("mcp-session-id", "")
        if session:
            headers["mcp-session-id"] = session
            client.post(
                MCP_URL,
                headers=headers,
                json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            )

        proof_query = (
            "What is the preferred governed InnerOS action workflow that includes "
            "explicit approval and a single-use execution permission?"
        )
        proof = mcp_call(
            client,
            headers,
            2,
            "recall",
            {"query": proof_query, "datasets": dataset, "top_k": 5},
        )
        proof_text = json.dumps(proof, ensure_ascii=False, default=str).lower()
        remote_v2_present = (
            "single-use" in proof_text
            and "approval" in proof_text
            and ("verify" in proof_text or "evidence" in proof_text)
        )

        remembered = None
        already_seeded = marker_file.exists() or remote_v2_present
        if not already_seeded:
            remembered = mcp_call(
                client,
                headers,
                3,
                "remember",
                {
                    "data": data,
                    "dataset_name": dataset,
                    "background": False,
                    "self_improvement": True,
                },
            )

        verify = mcp_call(
            client,
            headers,
            4,
            "recall",
            {
                "query": "Who is Ralphi, what are InnerChispa and PC Doctor, and what principles guide InnerOS?",
                "datasets": dataset,
                "top_k": 8,
            },
        )
        verify_text = json.dumps(verify, ensure_ascii=False, default=str)
        verify_lower = verify_text.lower()

    verified = (
        "innerchispa" in verify_lower
        and "pc" in verify_lower
        and "local" in verify_lower
        and not bool((verify.get("result") or {}).get("isError"))
    )

    if verified:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        marker_file.write_text(
            json.dumps(
                {
                    "dataset": dataset,
                    "seed_version": seed_version,
                    "facts_loaded": len(seed.get("facts", [])),
                    "verified": True,
                }
            ),
            encoding="utf-8",
        )

    result = {
        "ok": verified,
        "dataset": dataset,
        "seed_version": seed_version,
        "facts_loaded": len(seed.get("facts", [])),
        "already_seeded": already_seeded,
        "remote_v2_present": remote_v2_present,
        "remember_called": remembered is not None,
        "local_marker": marker_file.exists(),
        "recall_preview": verify_text[:2500],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
