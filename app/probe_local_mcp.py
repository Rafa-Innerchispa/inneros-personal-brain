from __future__ import annotations

import json
import httpx


def parse(text: str):
    vals=[]
    for line in text.splitlines():
        if line.startswith("data: "):
            try: vals.append(json.loads(line[6:]))
            except Exception: pass
    if vals: return vals[-1]
    try: return json.loads(text)
    except Exception: return {"raw": text[:2000]}


def main() -> int:
    url="http://127.0.0.1:8102/mcp"
    headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
    payload={
      "jsonrpc":"2.0","id":1,"method":"initialize",
      "params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"personal-brain","version":"0.1"}}
    }
    with httpx.Client(timeout=20) as c:
        r=c.post(url,headers=headers,json=payload)
        out={
          "status":r.status_code,
          "session":r.headers.get("mcp-session-id",""),
          "body":parse(r.text),
        }
    print(json.dumps(out,indent=2)[:12000])
    return 0 if 200 <= r.status_code < 300 else 2


if __name__=="__main__":
    raise SystemExit(main())
