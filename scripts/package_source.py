"""Create separate publication-source and private upstream-runtime archives."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/audit_upload.py")], cwd=ROOT, check=True)
names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
names = sorted(set(n for n in names if n and (ROOT / n).is_file()))
manifest = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names}
source = ROOT.parent / "hypospace-explorer-source.zip"
with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for name in names:
        z.write(ROOT / name, "hypospace-explorer/" + name)
    z.writestr("hypospace-explorer/RELEASE_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
lock = json.loads((ROOT / "upstream.lock.json").read_text())
runtime = ROOT.parent / "hypospace-upstream-runtime-private.zip"
with zipfile.ZipFile(runtime, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for name, expected in lock["files"].items():
        p = ROOT / ".cache/upstream" / name
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Upstream checksum mismatch before packaging")
        z.write(p, "hypospace-explorer/.cache/upstream/" + name)
    z.writestr("PRIVATE_RUNTIME_ONLY.txt", "Pinned upstream runtime cache for private server use. Do not add this archive or its contents to the public GitHub repository.\n")
print(f"Publication-source archive: {source.name} ({source.stat().st_size} bytes)")
print(f"Private upstream runtime archive: {runtime.name} ({runtime.stat().st_size} bytes)")
