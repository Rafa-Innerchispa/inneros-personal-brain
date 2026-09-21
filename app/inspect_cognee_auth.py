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
    e=load()
    spec=httpx.get(e["COGNEE_SERVICE_URL"].rstrip("/")+"/openapi.json",timeout=30).json()
    print(json.dumps(spec.get("components",{}).get("securitySchemes",{}),indent=2))


if __name__=="__main__":
    main()
