from __future__ import annotations

import hashlib
import json
import os
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value) -> None:
    data = json.dumps(value, ensure_ascii=False, indent=2)
    temp = path.with_name(path.name + ".tmp-" + uuid4().hex)
    with temp.open("w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, path)


def new_run(root: Path) -> Path:
    run = root / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    (run / "screenshots").mkdir()
    return run


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class Journal:
    def __init__(self, path: Path):
        self.path = path
        self.seq = 0
        self.lines = []

    def append(self, event: dict) -> None:
        self.seq += 1
        line = canonical({"seq": self.seq, "utc": utc(), **event}) + "\n"
        self.lines.append(line)
        # Publish complete snapshots only. Delayed append persistence on a
        # workspace-backed filesystem can otherwise overwrite a later rename.
        self.finalize()

    def finalize(self) -> None:
        """Atomically publish one complete snapshot after streaming append writes.

        This also avoids partial append snapshots in workspace-backed filesystems.
        Only used before the run is sealed; sealed evidence is never rewritten.
        """
        temp = self.path.with_name(self.path.name + ".final-" + uuid4().hex)
        with temp.open("w", encoding="utf-8") as f:
            f.writelines(self.lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, self.path)


def seal(run: Path) -> dict:
    manifest = {str(p.relative_to(run)): digest_file(p) for p in sorted(run.rglob("*")) if p.is_file() and p.name != "integrity.json"}
    write_json(run / "integrity.json", manifest)
    # A closed binary snapshot is the portable deliverable. Some hosted
    # workspaces synchronize repeatedly updated text files non-atomically.
    # Preserve the exact sealed bytes without ever re-sealing altered files.
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(run.rglob("*")):
            if p.is_file():
                archive.write(p, p.relative_to(run))
    archive_path = run.parent / (run.name + ".evidence.zip")
    with archive_path.open("xb") as f:
        f.write(payload.getvalue())
        f.flush()
        os.fsync(f.fileno())
    return manifest


def verify_integrity(run: Path) -> list[str]:
    try:
        expected = json.loads((run / "integrity.json").read_text())
    except (OSError, ValueError):
        return ["integrity manifest missing or invalid"]
    problems = []
    for name, sha in expected.items():
        p = (run / name).resolve()
        if not p.is_relative_to(run.resolve()) or not p.is_file() or digest_file(p) != sha:
            problems.append(name)
    actual = {str(p.relative_to(run)) for p in run.rglob("*") if p.is_file() and p.name != "integrity.json"}
    problems.extend(sorted(actual - set(expected)))
    return problems
