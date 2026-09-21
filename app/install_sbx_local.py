from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
import urllib.request
from pathlib import Path


VERSION = "0.43.0"
URL = (
    "https://editions.docker.com/linux/static/stable/x86_64/sbx/"
    f"docker-sbx_{VERSION}.tgz"
)
EXPECTED_SHA256 = "3eb15b8444e969aaa8d637250bef0f2bf90cb030aba0a7016a56b8e5fcdd25fe"


def main() -> int:
    root = Path(__file__).resolve().parent / ".runtime" / "docker-sbx"
    archive = root / f"docker-sbx_{VERSION}.tgz"
    extract = root / "bin"
    root.mkdir(parents=True, exist_ok=True)
    extract.mkdir(parents=True, exist_ok=True)

    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"sha256_mismatch:{digest}")

    with tarfile.open(archive, "r:gz") as tf:
        for member in tf.getmembers():
            target = (extract / member.name).resolve()
            if extract.resolve() not in target.parents and target != extract.resolve():
                raise RuntimeError("unsafe_tar_member")
        tf.extractall(extract, filter="data")

    candidates = list(extract.rglob("sbx"))
    if not candidates:
        raise RuntimeError("sbx_binary_not_found")

    sbx = candidates[0]
    sbx.chmod(sbx.stat().st_mode | 0o111)
    print(f"SBX_BIN={sbx}")
    print(f"VERSION={VERSION}")
    print(f"SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
