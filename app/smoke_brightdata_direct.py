from __future__ import annotations

import json
from pathlib import Path
import httpx


def load_env() -> dict[str,str]:
    p=Path("/home/rlopez/.config/inneros-personal-brain/runtime.env")
    out={}
    for line in p.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            k,v=line.split("=",1); out[k]=v
    return out


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
    e=load_env()
    token=e["BRIGHTDATA_API_TOKEN"]
    base=e.get("BRIGHTDATA_MCP_URL","https://mcp.brightdata.com/mcp")
    url=base+"?token="+httpx.QueryParams({"token":token})["token"]
    headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
    with httpx.Client(timeout=90, follow_redirects=True) as c:
        init=c.post(url,headers=headers,json={
            "jsonrpc":"2.0","id":1,"method":"initialize",
            "params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"inneros-personal-brain","version":"0.1"}}
        })
        session=init.headers.get("mcp-session-id","")
        if session:
            headers["mcp-session-id"]=session
            c.post(url,headers=headers,json={"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
        call=c.post(url,headers=headers,json={
            "jsonrpc":"2.0","id":2,"method":"tools/call",
            "params":{"name":"search_engine","arguments":{
                "query":"AI hackathons San Francisco September 2026",
                "engine":"google","geo_location":"us"
            }}
        })
        body=parse(call.text)
    result=(body.get("result") or {}) if isinstance(body,dict) else {}
    out={
        "init_status":init.status_code,
        "session":bool(session),
        "call_status":call.status_code,
        "is_error":bool(result.get("isError")),
        "content_preview":str(result.get("content") or "")[:5000],
    }
    print(json.dumps(out,indent=2))
    return 0 if call.status_code==200 and not out["is_error"] else 2


if __name__=="__main__":
    raise SystemExit(main())
