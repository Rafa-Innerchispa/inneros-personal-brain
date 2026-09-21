from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run(argv):
    p=subprocess.run(argv,capture_output=True,text=True,timeout=30,check=False)
    return {"returncode":p.returncode,"stdout":(p.stdout or "")[-12000:],"stderr":(p.stderr or "")[-12000:]}


def main():
    root=Path(__file__).resolve().parent/".runtime"/"docker-sbx"/"bin"
    sbx=str(list(root.rglob("sbx"))[0])
    out={
        "root":run([sbx,"--help"]),
        "run":run([sbx,"run","--help"]),
        "exec":run([sbx,"exec","--help"]),
        "shell":run([sbx,"run","shell","--help"]),
    }
    print(json.dumps(out,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
