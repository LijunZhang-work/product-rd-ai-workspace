#!/usr/bin/env python3
"""Thin, local evidence helpers. No C++ parser, call-graph engine or truth oracle.

Python 3.10+, standard library. Designed for WSL / Linux build environments.
Every output is new: existing report files and run directories are not overwritten.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

VERSION = "1.0.0"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def report(kind, errors=None, warnings=None, **data):
    return dict(schema_version=1, helper_version=VERSION, kind=kind,
                created_at=now(), errors=errors or [], warnings=warnings or [], **data)


def pairs(items):
    result = {}
    for item in items:
        if "=" not in item:
            raise ValueError("Expected NAME=/absolute/path: " + item)
        name, value = item.split("=", 1)
        if not name or name in result or not Path(value).is_absolute():
            raise ValueError("Invalid or duplicate mapping: " + item)
        result[name] = str(Path(value).resolve())
    return result


def within(path, root):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def checked_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("Evidence path must be relative to evidence root")
    p = (Path(root) / name).resolve()
    if not within(p, root) or not p.is_file():
        raise ValueError("Missing evidence file or path escapes evidence root: " + name)
    return p


def preflight(config):
    errors, warnings, tools = [], [], {}
    repos = config.get("repositories", {})
    for role in ("product", "emap"):
        value = repos.get(role, "")
        if not value or not Path(value).is_absolute() or not Path(value).is_dir():
            errors.append("repository unavailable: " + role)
    for name, executable in config.get("tools", {}).items():
        resolved = shutil.which(executable) if isinstance(executable, str) else None
        tools[name] = dict(requested=executable, resolved=resolved)
        if not resolved:
            (errors if name in config.get("required_tools", []) else warnings).append(
                "tool unavailable: " + name)
    for name in config.get("required_tools", []):
        if name not in tools:
            errors.append("required tool not configured: " + name)
    ids = []
    for target in config.get("targets", []):
        tid = target.get("id")
        if not tid or tid in ids:
            errors.append("missing or duplicate target id")
        ids.append(tid)
        for field in ("execution_domain", "compiler", "build_cwd", "compdb"):
            if not target.get(field):
                errors.append(str(tid) + ": missing " + field)
        for field in ("build_cwd", "compdb"):
            value = target.get(field, "")
            if not value or not Path(value).is_absolute() or not Path(value).exists():
                errors.append(str(tid) + ": unavailable " + field)
        if not shutil.which(target.get("compiler", "")):
            errors.append(str(tid) + ": compiler unavailable")
        if target.get("state") != "resolved":
            errors.append(str(tid) + ": target identity not marked resolved")
    if not ids:
        errors.append("no targets configured")
    return report("preflight", errors, warnings, tools=tools, target_ids=ids,
                  meaning="Availability only; compiler semantics and product identity require review")


def baseline(repo_paths):
    errors, rows = [], []
    for name, directory in repo_paths.items():
        row = dict(name=name, path=directory, snapshot_complete=False,
                   untracked_content_captured=False)
        if not Path(directory).is_dir():
            errors.append(name + ": directory missing")
        else:
            for key, argv in [
                ("head", ["rev-parse", "HEAD"]),
                ("status", ["status", "--porcelain=v1", "-z", "--untracked-files=all"]),
                ("diff", ["diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD", "--"]),
                ("submodules", ["submodule", "status", "--recursive"]),
            ]:
                try:
                    r = subprocess.run(["git", "-C", directory] + argv, capture_output=True,
                                       timeout=60, check=False)
                except (OSError, subprocess.TimeoutExpired) as e:
                    errors.append(name + ": " + str(e))
                    continue
                if r.returncode:
                    errors.append(name + ": git " + key + " failed")
                    row[key + "_stderr"] = r.stderr.decode(errors="replace")[:2000]
                elif key == "head":
                    row[key] = r.stdout.decode().strip()
                else:
                    row[key + "_sha256"] = digest_bytes(r.stdout)
                    if key == "status":
                        row["dirty"] = bool(r.stdout)
                    if key == "submodules":
                        row["submodule_status"] = r.stdout.decode(errors="replace").splitlines()
        rows.append(row)
    return report("baseline", errors, repositories=rows,
                  meaning="Git identity and dirty-state digests; archive needed inputs separately")


def audit_compdb(database, repos, keys):
    raw = read_json(database)
    if not isinstance(raw, list):
        raise ValueError("Compilation database must be a JSON array")
    errors, warnings, entries, groups = [], [], [], {}
    for a, root in repos.items():
        if not Path(root).is_dir():
            errors.append("repository root missing: " + a)
        for b, other in repos.items():
            if a < b and (within(root, other) or within(other, root)):
                errors.append("overlapping repository roots: " + a + ", " + b)
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"entry {index}: not an object")
            continue
        directory, source = item.get("directory"), item.get("file")
        if not isinstance(directory, str) or not Path(directory).is_absolute():
            errors.append(f"entry {index}: directory is not absolute")
            continue
        if not isinstance(source, str) or not source:
            errors.append(f"entry {index}: missing file")
            continue
        directory = str(Path(directory).resolve())
        source = str((Path(directory) / source).resolve())
        if not Path(directory).is_dir() or not Path(source).is_file():
            errors.append(f"entry {index}: unavailable directory/source: {source}")
        if "arguments" in item:
            argv = item["arguments"]
            if (not isinstance(argv, list) or not argv or
                    any(not isinstance(v, str) for v in argv)):
                errors.append(f"entry {index}: invalid arguments")
                continue
        elif isinstance(item.get("command"), str) and item["command"]:
            try:
                argv = shlex.split(item["command"], posix=True)
            except ValueError as e:
                errors.append(f"entry {index}: {e}")
                continue
            if not argv:
                errors.append(f"entry {index}: empty command")
                continue
            warnings.append(f"entry {index}: command inspected with POSIX tokenization; not replayed")
        else:
            errors.append(f"entry {index}: missing arguments/command")
            continue
        responses = []
        for arg in argv[1:]:
            if arg.startswith("@"):
                p = (Path(directory) / arg[1:]).resolve()
                exists = p.is_file()
                responses.append(dict(path=str(p), sha256=sha(p) if exists else None))
                if not exists:
                    errors.append(f"entry {index}: response file missing: {p}")
                warnings.append(f"entry {index}: response file semantics require actual compiler review")
        fingerprint = digest_bytes(json.dumps([directory, argv], ensure_ascii=False).encode())
        owners = [name for name, root in repos.items() if within(source, root)]
        entries.append(dict(index=index, file=source, directory=directory,
                            repositories=owners, command_sha256=fingerprint,
                            source_sha256=sha(source) if Path(source).is_file() else None,
                            arguments=argv, response_files=responses))
        groups.setdefault(source, set()).add(fingerprint)
    variants = {file: len(commands) for file, commands in groups.items() if len(commands) > 1}
    if variants:
        warnings.append("multiple commands per source: choose the intended target; do not take first entry")
    key_status = {str(Path(key).resolve()): str(Path(key).resolve()) in groups for key in keys}
    for key, present in key_status.items():
        if not present:
            errors.append("key translation unit not captured: " + key)
    if not raw:
        errors.append("empty compilation database")
    if not keys:
        warnings.append("no key translation units supplied; critical coverage has not been checked")
    return report("compdb_audit", errors, warnings, database=str(Path(database).resolve()),
                  database_sha256=sha(database), entry_count=len(raw), valid_entry_count=len(entries),
                  source_count=len(groups), multi_command_sources=variants,
                  repository_source_counts={name: len({e["file"] for e in entries if name in e["repositories"]})
                                            for name in repos},
                  key_translation_units=key_status, entries=entries,
                  meaning="Inventory of captured/configured commands, not proof of compilation or linking")


def compare_definitions(compdb_report, csv_path, keys, prefix_maps):
    audited = read_json(compdb_report)
    if audited.get("kind") != "compdb_audit":
        raise ValueError("Expected a compdb_audit report")
    errors, warnings = [], []
    if audited.get("errors"):
        errors.append("input compilation database audit contains errors")
    mappings = pairs(prefix_maps)
    sources = set()
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "file" not in reader.fieldnames:
            raise ValueError("Expected CSV column: file (Q00 function definition locations)")
        for row in reader:
            name = row.get("file", "")
            if not name:
                errors.append("empty definition file in CSV")
                continue
            for old in sorted(mappings, key=len, reverse=True):
                if name == old or name.startswith(old.rstrip("/") + "/"):
                    name = mappings[old] + name[len(old):]
                    break
            if not Path(name).is_absolute():
                errors.append("definition path is not absolute after mapping: " + name)
                continue
            sources.add(str(Path(name).resolve()))
    expected = {e["file"] for e in audited["entries"]}
    missing = sorted(expected - sources)
    if missing:
        warnings.append("some translation units have no listed function definition; inspect individually")
    key_status = {str(Path(p).resolve()): str(Path(p).resolve()) in sources for p in keys}
    for key, present in key_status.items():
        if not present:
            errors.append("key implementation has no extracted function definition: " + key)
    if not keys:
        warnings.append("no key implementation files supplied")
    return report("definition_presence", errors, warnings,
                  compdb_report_sha256=sha(compdb_report), csv_sha256=sha(csv_path),
                  prefix_maps=mappings, expected_source_count=len(expected),
                  observed_definition_file_count=len(sources),
                  missing_definition_files=missing, extra_definition_files=sorted(sources - expected),
                  key_implementation_files=key_status,
                  meaning="File-level definition presence only; not TU, variant, or path completeness")


def record_command(out, cwd, argv, target, inputs, timeout):
    if not argv or any(not isinstance(x, str) for x in argv):
        raise ValueError("No command arguments")
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    cwd = Path(cwd).resolve()
    if not cwd.is_dir():
        raise ValueError("Working directory does not exist")
    input_paths = [Path(p).resolve() for p in inputs]
    before = {str(p): sha(p) for p in input_paths}
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    metadata = dict(schema_version=1, helper_version=VERSION, kind="command_record", target=target,
                    started_at=now(), cwd=str(cwd), argv=argv, shell=False,
                    executable=shutil.which(argv[0], path=os.environ.get("PATH")),
                    inputs_before=before, timeout_seconds=timeout)
    started = time.monotonic()
    errors, state, returncode = [], "failed", None
    with (out / "stdout.txt").open("wb") as stdout, (out / "stderr.txt").open("wb") as stderr:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdout=stdout, stderr=stderr,
                                       start_new_session=(os.name == "posix"))
            try:
                returncode = process.wait(timeout=timeout)
                state = "succeeded" if returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                returncode = process.wait()
                state = "timed_out"
                errors.append("command timed out")
        except OSError as e:
            errors.append(str(e))
    after = {str(p): sha(p) if p.is_file() else None for p in input_paths}
    if before != after:
        errors.append("declared input files changed during command")
        state = "inputs_changed"
    metadata.update(finished_at=now(), elapsed_seconds=round(time.monotonic() - started, 3),
                    exit_code=returncode, status=state, errors=errors, inputs_after=after,
                    stdout_sha256=sha(out / "stdout.txt"), stderr_sha256=sha(out / "stderr.txt"),
                    meaning="Command execution record; exit zero does not establish analysis completeness")
    write_json(out / "run.json", metadata)
    return metadata


def validate_ledger(ledger, root):
    errors, warnings = [], []
    if ledger.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    baselines = ledger.get("baselines", {})
    targets = ledger.get("targets", [])
    if not baselines or not targets:
        errors.append("baselines and targets must be nonempty")
    evidence = {}
    for e in ledger.get("evidence", []):
        eid = e.get("id")
        if not eid or eid in evidence:
            errors.append("missing or duplicate evidence id: " + str(eid))
            continue
        evidence[eid] = e
        if e.get("kind") not in ("S", "C", "B", "R", "H"):
            errors.append(str(eid) + ": invalid evidence kind")
        if e.get("baseline_id") not in baselines:
            errors.append(str(eid) + ": unknown baseline")
        if not e.get("targets") or any(t not in targets for t in e["targets"]):
            errors.append(str(eid) + ": invalid targets")
        if not e.get("supports") or not e.get("limitations"):
            errors.append(str(eid) + ": supports/limitations required")
        try:
            path = checked_file(root, e.get("path"))
            if sha(path) != e.get("sha256"):
                errors.append(str(eid) + ": evidence digest mismatch")
        except (ValueError, OSError) as ex:
            errors.append(str(eid) + ": " + str(ex))
    scopes = {"source": {"S"}, "selected": {"S", "C"}, "linked": {"S", "C", "B"},
              "running": {"S", "C", "B", "R"}}
    claim_ids, pending = set(), []
    for c in ledger.get("claims", []):
        cid = c.get("id")
        if not cid or cid in claim_ids:
            errors.append("missing or duplicate claim id: " + str(cid))
        claim_ids.add(cid)
        status = c.get("status")
        if status not in ("verified", "inferred", "unknown", "conflict"):
            errors.append(str(cid) + ": invalid status")
        if c.get("scope") not in scopes or c.get("target") not in targets:
            errors.append(str(cid) + ": invalid scope/target")
        if not c.get("text") or not c.get("limitations"):
            errors.append(str(cid) + ": text/limitations required")
        if not c.get("baseline_ids") or any(b not in baselines for b in c["baseline_ids"]):
            errors.append(str(cid) + ": invalid baseline_ids")
        refs = c.get("evidence_ids", [])
        kinds = set()
        for eid in refs:
            e = evidence.get(eid)
            if e is None:
                errors.append(str(cid) + ": unknown evidence " + str(eid))
                continue
            kinds.add(e.get("kind"))
            if c.get("target") not in e.get("targets", []):
                errors.append(str(cid) + ": evidence target mismatch: " + str(eid))
            if e.get("baseline_id") not in c.get("baseline_ids", []):
                errors.append(str(cid) + ": evidence baseline mismatch: " + str(eid))
        if status == "verified":
            missing = scopes.get(c.get("scope"), set()) - kinds
            if missing:
                errors.append(str(cid) + ": missing evidence kinds " + ",".join(sorted(missing)))
            if not c.get("review_note"):
                errors.append(str(cid) + ": semantic review note required")
        else:
            pending.append(cid)
            if not c.get("gap") or not c.get("next_action"):
                errors.append(str(cid) + ": unresolved claims need gap and next_action")
            if status == "inferred" and not refs:
                errors.append(str(cid) + ": inferred claim requires supporting evidence")
    if not claim_ids:
        errors.append("no claims supplied")
    if pending:
        warnings.append("unresolved claims remain; mechanical checks are not project acceptance")
    return report("ledger_integrity", errors, warnings, evidence_count=len(evidence),
                  claim_count=len(claim_ids), unresolved_claims=pending, semantic_truth_checked=False,
                  meaning="Checks references, digests, target/baseline tags and minimum evidence classes only")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="action", required=True)
    a = sub.add_parser("preflight"); a.add_argument("--config", required=True); a.add_argument("--out", required=True)
    a = sub.add_parser("baseline"); a.add_argument("--repo", action="append", required=True); a.add_argument("--out", required=True)
    a = sub.add_parser("compdb"); a.add_argument("--db", required=True); a.add_argument("--repo", action="append", required=True)
    a.add_argument("--key", action="append", default=[]); a.add_argument("--out", required=True)
    a = sub.add_parser("compare-definitions"); a.add_argument("--compdb-report", required=True); a.add_argument("--csv", required=True)
    a.add_argument("--key", action="append", default=[]); a.add_argument("--map-prefix", action="append", default=[])
    a.add_argument("--out", required=True)
    a = sub.add_parser("record"); a.add_argument("--out-dir", required=True); a.add_argument("--cwd", required=True)
    a.add_argument("--target", required=True); a.add_argument("--input", action="append", default=[])
    a.add_argument("--timeout", type=float, default=600); a.add_argument("command", nargs=argparse.REMAINDER)
    a = sub.add_parser("validate-ledger"); a.add_argument("--ledger", required=True); a.add_argument("--evidence-root", required=True)
    a.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.action == "preflight":
            result = preflight(read_json(a.config))
        elif a.action == "baseline":
            result = baseline(pairs(a.repo))
        elif a.action == "compdb":
            result = audit_compdb(a.db, pairs(a.repo), a.key)
        elif a.action == "compare-definitions":
            result = compare_definitions(a.compdb_report, a.csv, a.key, a.map_prefix)
        elif a.action == "validate-ledger":
            result = validate_ledger(read_json(a.ledger), a.evidence_root)
        else:
            command = a.command[1:] if a.command[:1] == ["--"] else a.command
            result = record_command(a.out_dir, a.cwd, command, a.target, a.input, a.timeout)
            print(json.dumps({"status": result["status"], "record": str(Path(a.out_dir) / "run.json")}, ensure_ascii=False))
            return 0 if result["status"] == "succeeded" else 2
        write_json(a.out, result)
        print(json.dumps({"report": a.out, "errors": len(result["errors"]), "warnings": len(result["warnings"])}, ensure_ascii=False))
        return 2 if result["errors"] else 0
    except (ValueError, TypeError, KeyError, OSError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
