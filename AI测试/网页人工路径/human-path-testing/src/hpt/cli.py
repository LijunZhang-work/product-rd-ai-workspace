from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from pydantic import ValidationError
from playwright.sync_api import Error as BrowserError

from .contracts import Route, Behavior, Environment, PolicyError, read_json, validate_bundle
from .evidence import write_json, verify_integrity, new_run, seal
from .models import ModelClient, ModelConfig, StdioModel


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def client(path):
    return ModelClient(ModelConfig.model_validate(read_json(path))) if path else None


def load_case(folder):
    p = Path(folder)
    return Route.model_validate(read_json(p / "route.json")), Behavior.model_validate(read_json(p / "behavior.json")), Environment.model_validate(read_json(p / "environment.json")), read_json(p / "inputs.json")


def exit_result(r):
    return {"PASS": 0, "FAIL": 1, "INCOMPLETE": 3, "BLOCKED": 4, "UNSUPPORTED": 5}[r["overall"]]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hpt", description="Constrained UI routes, evidence, image-first exploration and replay. No complete human-equivalence certification.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init-demo", help="Create a fresh example case directory")
    p.add_argument("destination", type=Path)
    p.add_argument("--case", default="create")
    p.add_argument("--base-url", default="http://127.0.0.1:8765")
    p.add_argument("--functional-only", action="store_true")
    p = sub.add_parser("fixture", help="Run local fixture, never production")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--mode", default="normal")
    p.add_argument("--database", default=":memory:")
    p = sub.add_parser("doctor")
    p.add_argument("--model", type=Path)
    for command in ["validate", "run"]:
        p = sub.add_parser(command)
        p.add_argument("case", type=Path)
        p.add_argument("--output", type=Path, default=Path("artifacts"))
        if command == "run":
            p.add_argument("--vision-model", type=Path)
    p = sub.add_parser("demo", help="Create a fresh in-memory fixture and execute one case")
    p.add_argument("--case", default="create")
    p.add_argument("--mode", default="normal")
    p.add_argument("--output", type=Path, default=Path("artifacts"))
    p.add_argument("--functional-only", action="store_true")
    p.add_argument("--vision-model", type=Path)
    for command in ["report", "integrity"]:
        p = sub.add_parser(command)
        p.add_argument("run", type=Path)
    p = sub.add_parser("compare")
    p.add_argument("old", type=Path)
    p.add_argument("new", type=Path)
    p = sub.add_parser("review", help="Add an external visual assessment without changing original result")
    p.add_argument("run", type=Path)
    p.add_argument("review", type=Path)
    p.add_argument("--output", type=Path, default=Path("assessments"))
    p = sub.add_parser("explore")
    p.add_argument("--intent", required=True, type=Path)
    p.add_argument("--environment", required=True, type=Path)
    p.add_argument("--parameters", required=True, type=Path)
    p.add_argument("--inputs", required=True, type=Path)
    model_choice = p.add_mutually_exclusive_group(required=True)
    model_choice.add_argument("--model", type=Path)
    model_choice.add_argument("--stdio", action="store_true")
    p.add_argument("--max-actions", type=int, default=30)
    p.add_argument("--output", type=Path, default=Path("explorations"))
    p = sub.add_parser("compile", help="Text-only route maintenance against frozen business contract")
    p.add_argument("case", type=Path)
    p.add_argument("--model", required=True, type=Path)
    p.add_argument("--destination", required=True, type=Path)
    p = sub.add_parser("prepare-case", help="Attach separate expected outcomes to an exploration candidate")
    p.add_argument("exploration", type=Path)
    p.add_argument("--outcomes", required=True, type=Path)
    p.add_argument("--destination", required=True, type=Path)
    p = sub.add_parser("publish")
    p.add_argument("case", type=Path)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--runs", required=True, nargs="+", type=Path)
    p = sub.add_parser("recommend")
    p.add_argument("case_id")
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--inputs", required=True, type=Path)
    p = sub.add_parser("schema")
    p.add_argument("destination", type=Path)
    p = sub.add_parser("regression")
    p.add_argument("suite", type=Path, help="JSON list of case directory paths, relative to suite file")
    p.add_argument("--output", type=Path, default=Path("artifacts"))
    p.add_argument("--vision-model", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init-demo":
            from .examples import save_example
            emit({"directory": str(save_example(args.destination, args.case, args.base_url, not args.functional_only).resolve())})
        elif args.command == "fixture":
            from .fixture import serve_fixture
            with serve_fixture(args.mode, args.port, args.database) as (_, url):
                print(url, flush=True)
                while True:
                    time.sleep(1)
        elif args.command == "doctor":
            from playwright.sync_api import sync_playwright
            status = {"python": sys.version, "model_configured": bool(args.model), "browser": "not_checked"}
            with sync_playwright() as p:
                b = p.chromium.launch(executable_path=os.environ.get("HPT_CHROMIUM_EXECUTABLE") or None)
                status.update(browser="launch_ok", browser_version=b.version)
                b.close()
            if args.model:
                cfg = ModelConfig.model_validate(read_json(args.model))
                status.update(model=cfg.model, supports_images=cfg.supports_images, credential_present=bool(os.environ.get(cfg.api_key_env)), model_live_call="not_performed")
            emit(status)
        elif args.command in {"run", "validate"}:
            route, behavior, env, inputs = load_case(args.case)
            validate_bundle(route, behavior, inputs)
            if args.command == "validate":
                emit({"valid": True, "case_id": route.case_id, "oracle_status": behavior.oracle_status, "note": "Validation does not execute a browser or verify product behavior."})
            else:
                from .runner import execute
                run, r = execute(route, behavior, env, inputs, args.output, client(args.vision_model))
                emit({"run": str(run.resolve()), **r})
                return exit_result(r)
        elif args.command == "demo":
            from .examples import make_case, seed_case
            from .fixture import serve_fixture
            from .runner import execute
            with serve_fixture(args.mode) as (fixture, url):
                route, behavior, env, inputs = make_case(args.case, url, not args.functional_only)
                seed_case(fixture, args.case, inputs)
                run, r = execute(route, behavior, env, inputs, args.output, client(args.vision_model))
            emit({"run": str(run.resolve()), **r})
            return exit_result(r)
        elif args.command == "report":
            emit({"result": read_json(args.run / "result.json"), "integrity_issues": verify_integrity(args.run)})
        elif args.command == "integrity":
            issues = verify_integrity(args.run)
            emit({"integrity": "fail" if issues else "pass", "issues": issues})
            return 1 if issues else 0
        elif args.command == "compare":
            from .reporting import compare_runs
            emit(compare_runs(args.old, args.new))
        elif args.command == "review":
            from .vision import import_review
            folder, result = import_review(args.run, read_json(args.review), args.output)
            emit({"assessment": str(folder.resolve()), **result})
        elif args.command == "explore":
            from .explorer import explore
            folder, status = explore(args.intent.read_text(encoding="utf-8"), Environment.model_validate(read_json(args.environment)), read_json(args.parameters), read_json(args.inputs), StdioModel() if args.stdio else client(args.model), args.output, args.max_actions)
            emit({"exploration": str(folder.resolve()), "status": status, "verified": False})
            return 0 if status == "candidate" else 3
        elif args.command == "compile":
            from .explorer import compile_candidate
            route, behavior, _, inputs = load_case(args.case)
            answer = compile_candidate(route, behavior, inputs, client(args.model), args.destination)
            emit({"candidate": str(args.destination.resolve()), "case_id": answer.case_id, "verified": False})
        elif args.command == "prepare-case":
            from .explorer import prepare_case, OutcomeSpec
            route = prepare_case(args.exploration, OutcomeSpec.model_validate(read_json(args.outcomes)), args.destination)
            emit({"case": str(args.destination.resolve()), "case_id": route.case_id, "replay_verified": False})
        elif args.command == "publish":
            from .registry import publish
            route, behavior, _, _ = load_case(args.case)
            emit(publish(args.registry, route, behavior, args.runs))
        elif args.command == "recommend":
            from .registry import recommend
            emit(recommend(args.registry, args.case_id, read_json(args.inputs)))
        elif args.command == "schema":
            args.destination.mkdir(parents=True, exist_ok=False)
            for name, model in [("route", Route), ("behavior", Behavior), ("environment", Environment), ("model", ModelConfig)]:
                write_json(args.destination / f"{name}.schema.json", model.model_json_schema())
            emit({"schemas": str(args.destination.resolve()), "note": "Cross-reference checks also require hpt validate."})
        elif args.command == "regression":
            from .runner import execute
            paths = read_json(args.suite)
            if not isinstance(paths, list) or not 1 <= len(paths) <= 100 or any(type(x) is not str for x in paths):
                raise PolicyError("suite must contain 1..100 case directory paths")
            results = []
            model = client(args.vision_model)
            for path in paths:
                route, behavior, env, inputs = load_case(args.suite.parent / path)
                folder, result = execute(route, behavior, env, inputs, args.output, model)
                results.append({"case": path, "run": str(folder.resolve()), "overall": result["overall"]})
                print(json.dumps(results[-1]), flush=True)
            summary = new_run(args.output)
            write_json(summary / "suite.json", results)
            seal(summary)
            emit({"suite_report": str(summary.resolve()), "runs": len(results), "pass": sum(r["overall"] == "PASS" for r in results)})
            return 0 if all(r["overall"] == "PASS" for r in results) else 3
        return 0
    except KeyboardInterrupt:
        return 130
    except (PolicyError, ValidationError, ValueError, OSError, KeyError, BrowserError) as e:
        rejection = {"status": "REJECTED_OR_BLOCKED", "error_type": type(e).__name__, "error": str(e)[:3000]}
        if getattr(args, "output", None):
            run = new_run(args.output)
            write_json(run / "rejection.json", rejection)
            seal(run)
            rejection["evidence"] = str(run.resolve())
        emit(rejection)
        return 2
