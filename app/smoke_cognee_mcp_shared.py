from __future__ import annotations

import json
import httpx


MCP_URL = "http://127.0.0.1:8241/mcp"


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


def main() -> int:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    with httpx.Client(timeout=60) as client:
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
                    "clientInfo": {
                        "name": "inneros-agent-fabric-smoke",
                        "version": "0.1",
                    },
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

        listed = client.post(
            MCP_URL,
            headers=headers,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        listed.raise_for_status()
        tools_body = parse_sse(listed.text)
        tools = (
            (tools_body.get("result") or {}).get("tools") or []
            if isinstance(tools_body, dict)
            else []
        )
        names = [t.get("name") for t in tools if isinstance(t, dict)]

        recalled = client.post(
            MCP_URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "recall",
                    "arguments": {
                        "query_text": "What does InnerOS Personal Brain remember about Physical Guardian, VoiceOps, and the Battle of the Personal Brains demo?",
                        "datasets": ["inneros-personal-brain"],
                        "top_k": 6,
                    },
                },
            },
        )
        recalled.raise_for_status()
        recall_body = parse_sse(recalled.text)
        result = recall_body.get("result") if isinstance(recall_body, dict) else None

    serialized = json.dumps(result, ensure_ascii=False, default=str)
    out = {
        "ok": all(name in names for name in ("remember", "recall", "forget")),
        "session": bool(session),
        "tools": names,
        "recall_has_content": bool(serialized and serialized != "null"),
        "recall_preview": serialized[:3500],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] and out["recall_has_content"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
