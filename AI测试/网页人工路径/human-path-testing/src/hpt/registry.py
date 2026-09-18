"""Immutable local route versions. Publication requires matching replay evidence."""
from __future__ import annotations
import json
from pathlib import Path
from .contracts import Route, Behavior, PolicyError, validate_bundle
from .evidence import canonical, digest_bytes, verify_integrity, write_json


def route_hash(route):
    return digest_bytes(canonical(route.model_dump()).encode())


def publish(root: Path, route: Route, behavior: Behavior, runs: list[Path]):
    root.mkdir(parents=True, exist_ok=True)
    case_root = root / route.case_id
    case_root.mkdir(exist_ok=True)
    destination = case_root / f"v{route.revision}"
    if destination.exists():
        raise PolicyError("registry version already exists; publication never overwrites")
    verified_inputs = {}
    for run in runs:
        if verify_integrity(run):
            raise PolicyError("replay evidence integrity failed")
        result = json.loads((run / "result.json").read_text())
        saved_route = Route.model_validate(json.loads((run / "route.json").read_text()))
        saved_behavior = Behavior.model_validate(json.loads((run / "behavior.json").read_text()))
        inputs = json.loads((run / "inputs.json").read_text())
        validate_bundle(route, behavior, inputs)
        if result["overall"] != "PASS" or route_hash(route) != route_hash(saved_route) or behavior != saved_behavior:
            raise PolicyError("publication requires PASS from exactly this route and behavior contract")
        verified_inputs[canonical(inputs)] = str(run.resolve())
    if not verified_inputs:
        raise PolicyError("at least one exact replay is required")
    index_path = case_root / "active.json"
    if index_path.exists():
        old = json.loads(index_path.read_text())
        if route.revision <= old["revision"]:
            raise PolicyError("revision must increase")
        for value in old["verified_inputs"]:
            if value not in verified_inputs:
                raise PolicyError("old input coverage must be replayed on the new route before publication")
    destination.mkdir(exist_ok=False)
    write_json(destination / "route.json", route.model_dump())
    write_json(destination / "behavior.json", behavior.model_dump())
    record = {"case_id": route.case_id, "revision": route.revision, "route_sha256": route_hash(route), "verified_inputs": verified_inputs, "scope": "Local runner UI checks only; no host isolation certification."}
    write_json(destination / "verification.json", record)
    write_json(index_path, record)
    return record


def recommend(root: Path, case_id: str, inputs: dict):
    # Never use unvalidated text as a filesystem path.
    import re
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", case_id) or case_id in {".", ".."}:
        raise PolicyError("invalid case id")
    p = root / case_id / "active.json"
    if not p.exists():
        return {"verdict": "skip", "reason": "no active route"}
    data = json.loads(p.read_text())
    route_file = p.parent / f"v{data['revision']}" / "route.json"
    route = Route.model_validate(json.loads(route_file.read_text()))
    if route_hash(route) != data["route_sha256"]:
        raise PolicyError("registry route changed")
    return {"verdict": "run" if canonical(inputs) in data["verified_inputs"] else "adapt", "route": str(route_file.resolve()), "reason": "Exact tested inputs matched" if canonical(inputs) in data["verified_inputs"] else "New inputs require an independent replay before verified reuse"}

