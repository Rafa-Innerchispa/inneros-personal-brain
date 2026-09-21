from __future__ import annotations

import json
import shutil
import subprocess


def run(argv):
    try:
        p=subprocess.run(argv,capture_output=True,text=True,timeout=10,check=False)
        return {"ok":p.returncode==0,"returncode":p.returncode,"stdout":(p.stdout or "")[-2000:],"stderr":(p.stderr or "")[-2000:]}
    except Exception as exc:
        return {"ok":False,"error":f"{type(exc).__name__}: {exc}"}


def main():
    ngrok=shutil.which("ngrok")
    out={"ngrok_path":ngrok}
    if ngrok:
        out["version"]=run([ngrok,"version"])
        out["config_check"]=run([ngrok,"config","check"])
    print(json.dumps(out,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
