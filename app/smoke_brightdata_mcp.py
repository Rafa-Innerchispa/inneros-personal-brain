from __future__ import annotations

import json
import httpx


MCP_URL = "http://127.0.0.1:8102/mcp"


def parse(text: str):
    vals=[]
    for line in text.splitlines():
        if line.startswith("data: "):
            try: vals.append(json.loads(line[6:]))
            except Exception: pass
    if vals: return vals[-1]
    try: return json.loads(text)
    except Exception: return {"raw": text[:4000]}


def main() -> int:
    headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
    with httpx.Client(timeout=90) as c:
        init=c.post(MCP_URL,headers=headers,json={
            "jsonrpc":"2.0","id":1,"method":"initialize",
            "params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"personal-brain","version":"0.1"}}
        })
        session=init.headers.get("mcp-session-id","")
        if session:
            headers["mcp-session-id"]=session
            c.post(MCP_URL,headers=headers,json={"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        call=c.post(MCP_URL,headers=headers,json={
            "jsonrpc":"2.0","id":2,"method":"tools/call",
            "params":{"name":"brightdata_search_engine","arguments":{
                "query":"AI hackathons San Francisco September 2026",
                "engine":"google","geo_location":"us","dry_run":False
            }}
        })
        body=parse(call.text)
    out={"status":call.status_code,"session":bool(session),"body":body}
    print(json.dumps(out,indent=2)[:12000])
    text=json.dumps(body)
    return 0 if call.status_code==200 and '"isError": true' not in text else 2


if __name__=="__main__":
    raise SystemExit(main())
