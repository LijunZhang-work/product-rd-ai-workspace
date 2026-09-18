#!/usr/bin/env python3
"""Check package navigation and declared workflow coverage, not evidence truth.

No installation, Docker operation, product build, query, or source mutation is run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

KIT = Path(__file__).resolve().parents[1]
MANIFEST = KIT / "config/workflow.json"
STATUSES = {"pending", "completed", "reused", "partial", "blocked", "not_applicable"}
SHARED_DEPENDENCIES = {
    "../../工具接入与共享能力/工具统一管理与使用指南.md",
    "../../工具接入与共享能力/工具状态与验收报告.md",
}
TOOL_RUN_STEPS = {"S03", "S05", "S06", "S07", "S10", "S12"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def signature(manifest):
    payload = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def expected_rows(manifest, mode, configurations):
    if mode not in ("preparation", "full"):
        raise ValueError("Unknown mode")
    if not isinstance(configurations, list) or any(
        not isinstance(c, str) or not c.strip() or c == "global" or "REPLACE" in c
        for c in configurations
    ) or len(set(configurations)) != len(configurations):
        raise ValueError("Configuration IDs must be unique, non-placeholder strings")
    if mode == "full" and not configurations:
        raise ValueError("Full scope needs at least one verified build configuration ID")
    if mode == "preparation" and configurations:
        raise ValueError("Preparation scope does not declare build configurations")
    rows = {}
    for step in manifest["steps"]:
        if mode == "preparation" and not step["preparation"]:
            continue
        scopes = configurations if step["scope"] == "configuration" else ["global"]
        for scope in scopes:
            rows[(step["id"], scope)] = step
    return rows


def initial_state(manifest, mode, configurations):
    rows = expected_rows(manifest, mode, configurations)
    return {
        "schema_version": 1, "workflow_version": manifest["version"],
        "manifest_sha256": signature(manifest), "mode": mode,
        "config_ids": configurations,
        "tool_report_reference": "",
        "tasks": [dict(step_id=step, scope=scope, status="pending", reason="", evidence=[],
                       **({"task_run_evidence": []} if step in TOOL_RUN_STEPS else {}))
                  for step, scope in rows],
    }


def check_state(manifest, state, root, expected_mode=None):
    root = Path(root).resolve()
    errors = []
    if not isinstance(state, dict):
        raise ValueError("State must be a JSON object")
    if state.get("schema_version") != 1:
        errors.append("Unsupported state schema")
    if state.get("manifest_sha256") != signature(manifest) or state.get("workflow_version") != manifest["version"]:
        errors.append("State does not match this package's workflow manifest")
    mode = state.get("mode")
    if expected_mode is not None and expected_mode != mode:
        errors.append("Declared scope differs from requested scope")
    expected = expected_rows(manifest, mode, state.get("config_ids"))
    tasks = state.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("tasks must be an array")
    def check_file_reference(name, label):
        if not isinstance(name, str) or not name or Path(name).is_absolute():
            errors.append(label + ": evidence must be a relative file path")
            return
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.stat().st_size == 0:
            errors.append(label + ": missing, empty, or out-of-root evidence: " + name)

    # This is an applicability/reference index whose contract belongs to the
    # shared tool guide. Do not duplicate the registry's status schema here.
    check_file_reference(state.get("tool_report_reference"), "tool_report_reference")
    seen = set()
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("Invalid task object")
            continue
        sid, scope = task.get("step_id"), task.get("scope")
        if not isinstance(sid, str) or not isinstance(scope, str):
            errors.append("Task ID/scope must be strings")
            continue
        key = (sid, scope)
        label = sid + "/" + scope
        if key in seen:
            errors.append(label + ": duplicate task")
        seen.add(key)
        if key not in expected:
            errors.append(label + ": unexpected task")
            continue
        status = task.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(label + ": invalid status")
            continue
        if status in {"pending", "partial", "blocked"}:
            errors.append(label + ": not complete (" + status + ")")
        if status == "not_applicable" and not expected[key]["allow_not_applicable"]:
            errors.append(label + ": required step cannot be skipped")
        if status in {"reused", "partial", "blocked", "not_applicable"} and (not isinstance(task.get("reason"), str) or not task["reason"].strip()):
            errors.append(label + ": reason required")
        evidence = task.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(label + ": evidence must be an array")
            continue
        if status in {"completed", "reused", "not_applicable"} and not evidence:
            errors.append(label + ": evidence required")
        for name in evidence:
            check_file_reference(name, label)
        if sid in TOOL_RUN_STEPS and status in {"completed", "reused"}:
            runs = task.get("task_run_evidence")
            if not isinstance(runs, list) or not runs:
                errors.append(label + ": task_run_evidence required; installation alone is insufficient")
            else:
                for name in runs:
                    check_file_reference(name, label + "/task_run_evidence")
    for sid, scope in expected.keys() - seen:
        errors.append(sid + "/" + scope + ": missing task")
    return {
        "kind": "workflow_coverage", "mode": mode,
        "workflow_records_complete": not errors, "errors": errors,
        "expected_tasks": len(expected), "recorded_tasks": len(tasks),
        "tool_readiness_checked": False, "tool_execution_checked": False,
        "semantic_truth_checked": False,
        "meaning": "Checks declarations and local evidence files only; inspect their contents using 03.",
    }


def check_package(root, manifest):
    root = Path(root).resolve()
    errors, graph = [], {}
    # Shared documents live in the workspace-shaped delivery, not an arbitrary
    # parent directory named by a manifest. Restrict names and resolved targets
    # (including symlinks); checking their presence says nothing about readiness.
    shared_files = set()
    shared_names = manifest.get("shared_dependencies", [])
    if not isinstance(shared_names, list):
        errors.append("shared_dependencies must be an array")
        shared_names = []
    if manifest.get("version") == "1.2" and set(
        name for name in shared_names if isinstance(name, str)
    ) != SHARED_DEPENDENCIES:
        errors.append("Required shared tool guide/report declarations are missing or invalid")
    shared_root = root.parent.parent / "工具接入与共享能力"
    for name in shared_names:
        if not isinstance(name, str) or name not in SHARED_DEPENDENCIES:
            errors.append("Disallowed shared dependency: " + str(name))
            continue
        expected = shared_root / Path(name).name
        resolved = (root / name).resolve()
        if resolved != expected or not resolved.is_file() or resolved.stat().st_size == 0:
            errors.append("Missing, empty, or out-of-location shared dependency: " + name)
            continue
        shared_files.add(resolved)
    for name in manifest["required_files"]:
        p = (root / name).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            errors.append("Missing required package file: " + name)
    docs = {p.resolve(): p for p in root.glob("*.md")}
    for path in docs:
        graph[path] = []
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("#"):
                continue
            link = link.split("#", 1)[0]
            dest = (path.parent / link).resolve()
            if not dest.exists() or (not dest.is_relative_to(root) and dest not in shared_files):
                errors.append("Broken local link: " + path.name + " -> " + link)
            if dest in docs:
                graph[path].append(dest)
    visited = set()
    stack = [(root / manifest["entry"]).resolve()]
    while stack:
        path = stack.pop()
        if path in visited:
            continue
        visited.add(path)
        stack.extend(graph.get(path, []))
    for path in docs.keys() - visited:
        errors.append("Document unreachable from entry: " + path.name)
    return {"kind": "package_navigation", "ok": not errors, "errors": errors,
            "documents": len(docs), "reachable_documents": len(visited & docs.keys()),
            "shared_documents": len(shared_files),
            "tool_readiness_checked": False, "tool_execution_checked": False,
            "semantic_truth_checked": False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)
    a = sub.add_parser("package"); a.add_argument("--out", required=True)
    a = sub.add_parser("init"); a.add_argument("--mode", choices=["preparation", "full"], required=True)
    a.add_argument("--config-id", action="append", default=[]); a.add_argument("--out", required=True)
    a = sub.add_parser("check"); a.add_argument("--state", required=True); a.add_argument("--root", required=True)
    a.add_argument("--expected-mode", choices=["preparation", "full"], required=True)
    a.add_argument("--out", required=True)
    args = p.parse_args(argv)
    try:
        manifest = read_json(MANIFEST)
        if args.action == "package":
            result = check_package(KIT, manifest)
        elif args.action == "init":
            result = initial_state(manifest, args.mode, args.config_id)
        else:
            result = check_state(manifest, read_json(args.state), args.root, args.expected_mode)
        # Never replace an earlier result or progress file implicitly.
        with Path(args.out).open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps({"output": str(Path(args.out).resolve()),
                          "errors": result.get("errors", [])}, ensure_ascii=False))
        return 2 if result.get("errors") else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
