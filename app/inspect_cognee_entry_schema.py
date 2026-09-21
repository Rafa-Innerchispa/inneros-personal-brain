from __future__ import annotations

import json
from pathlib import Path
import httpx


def env():
    p=Path(__file__).resolve().parent/".runtime"/"cognee.env"
    out={}
    for line in p.read_text().splitlines():
        if "=" in line:
            k,v=line.split("=",1); out[k]=v
    return out


def main():
    e=env()
    h={"X-Api-Key":e["COGNEE_API_KEY"],"Authorization":f"Bearer {e['COGNEE_API_KEY']}"}
    spec=httpx.get(e["COGNEE_SERVICE_URL"].rstrip("/")+"/openapi.json",headers=h,timeout=30).json()
    paths=spec["paths"]
    schemas=spec["components"]["schemas"]
    picked={}
    for p in ["/api/v1/remember/entry","/api/v1/remember","/api/v1/recall"]:
        picked[p]=paths.get(p,{})
    refs={k:v for k,v in schemas.items() if k in [
        "MemoryEntryDTO","RememberEntryDTO","RecallPayloadDTO","Body_remember_api_v1_remember_post"
    ] or "remember" in k.lower() or "recall" in k.lower()}
    print(json.dumps({"paths":picked,"schemas":refs},indent=2)[:30000])


if __name__=="__main__":
    main()
