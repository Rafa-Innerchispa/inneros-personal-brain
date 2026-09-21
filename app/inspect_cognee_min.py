from __future__ import annotations

import json
from pathlib import Path
import httpx


def load():
    p=Path(__file__).resolve().parent/".runtime"/"cognee.env"
    d={}
    for line in p.read_text().splitlines():
        if "=" in line:
            k,v=line.split("=",1); d[k]=v
    return d


def main():
    e=load(); h={"X-Api-Key":e["COGNEE_API_KEY"],"Authorization":f"Bearer {e['COGNEE_API_KEY']}"}
    spec=httpx.get(e["COGNEE_SERVICE_URL"].rstrip("/")+"/openapi.json",headers=h,timeout=30).json()
    op=spec["paths"]["/api/v1/remember"]["post"]
    body=op["requestBody"]["content"]
    schema=spec["components"]["schemas"]["Body_remember_api_v1_remember_post"]
    props={}
    for k,v in schema.get("properties",{}).items():
        props[k]={"type":v.get("type"),"anyOf":v.get("anyOf"),"default":v.get("default")}
    print(json.dumps({"content_types":list(body.keys()),"required":schema.get("required",[]),"properties":props},indent=2))


if __name__=="__main__":
    main()
