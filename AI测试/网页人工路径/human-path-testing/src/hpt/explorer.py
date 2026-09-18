"""Bounded image-first exploration. Outputs candidates, never auto-publishes."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import Field
from .contracts import Strict, Target, Step, Route, Behavior, Parameter, Assertion, Checkpoint, PolicyError
from .runner import Driver
from .evidence import new_run, write_json, Journal, seal, digest_file


class ExplorationDecision(Strict):
    observation_id: int
    done: bool = False
    business_id: str
    explanation: str = Field(min_length=1, max_length=2000)
    action: Literal["click", "hover", "fill_text", "type_text", "press_key", "select_native", "check", "uncheck", "scroll", "reload", "go_back"] | None = None
    target: Target | None = None
    param: str | None = None
    key: str | None = None
    scroll_y: int | None = None


def explore(intent: str, env, parameters: dict, inputs: dict, client, output: Path, max_actions=30):
    if not client.config.supports_images:
        raise PolicyError("image-first exploration requires an image-capable model")
    if not 1 <= max_actions <= 60:
        raise PolicyError("exploration action budget must be 1..60")
    run = new_run(output)
    params = {k: Parameter.model_validate(v) for k, v in parameters.items()}
    route = Route(case_id="explored", revision=1, summary=intent, parameters=params, targets={}, checkpoints={}, steps=[Step(id="S01", business_id="entry", action="open_entry")])
    behavior = Behavior(case_id="explored", revision=1, original_intent=intent, oracle_status="pending", required_steps=route.steps, required_targets={}, required_checkpoints={}, excluded=["Candidate only: add independent outcome assertions before publication."])
    from .contracts import validate_bundle
    validate_bundle(route, behavior, inputs)
    driver = Driver(route, behavior, env, inputs, run)
    write_json(run / "environment.json", env.model_dump())
    write_json(run / "inputs.json", inputs)
    calls = Journal(run / "model_calls.jsonl")
    history = []
    status, error = "action_budget_exhausted", None
    try:
        driver.start()
        driver.perform(route.steps[0])
        for i in range(max_actions):
            shot = driver.capture("explore")
            snapshot = driver.page.locator("body").aria_snapshot()[:18000]
            prompt = "Explore the user's UI workflow using only the supplied action schema. See the attached current screenshot. Do not call APIs, inject JS, change storage, force clicks or bypass declared navigation. Use named parameters for input. done only means exploration candidate finished, not verified. For text input click the field first. Target scope must be null or an existing target id. Return exact JSON following this schema: " + json.dumps(ExplorationDecision.model_json_schema()) + "\nTask: " + intent + "\nInputs: " + json.dumps(inputs) + "\nObservation ID: " + str(shot["observation_id"]) + "\nTargets: " + json.dumps({k: v.model_dump() for k, v in route.targets.items()}) + "\nARIA:\n" + snapshot + "\nRecent actions: " + json.dumps(history[-8:])
            raw = client.complete_json(prompt, run / shot["screenshot"])
            decision = ExplorationDecision.model_validate(raw)
            calls.append({"decision": decision.model_dump(), "receipt": client.last_receipt, "observation": shot})
            if decision.observation_id != shot["observation_id"]:
                raise PolicyError("stale observation id")
            if decision.done:
                if any(x is not None for x in [decision.action, decision.target, decision.param, decision.key, decision.scroll_y]):
                    raise PolicyError("done decision cannot carry an action")
                status = "candidate"
                break
            ref = None
            if decision.target:
                ref = f"T{i+1:03d}"
                route.targets[ref] = decision.target
            data = {"id": f"S{len(route.steps)+1:02d}", "business_id": decision.business_id, "action": decision.action, "target": ref, "param": decision.param, "key": decision.key, "scroll_y": decision.scroll_y}
            step = Step.model_validate(data)
            route.steps.append(step)
            route = Route.model_validate(route.model_dump())
            driver.route = route
            driver.perform(step)
            history.append({"action": step.model_dump(), "explanation": decision.explanation})
    except Exception as e:
        status, error = "failed", str(e)[:3000]
    finally:
        try:
            close_errors = driver.close()
        except Exception as e:
            close_errors = [str(e)]
        for journal in [driver.events, driver.assertions, driver.diagnostics, calls]:
            try:
                journal.finalize()
            except Exception as e:
                close_errors.append(str(e))
        write_json(run / "candidate_route.json", route.model_dump())
        write_json(run / "exploration.json", {"status": status, "error": error, "close_errors": close_errors, "intent": intent, "image_first": True, "verified": False, "note": "A candidate must receive independent expected results and clean replay; model done is not PASS."})
        seal(run)
    return run, status


def compile_candidate(route: Route, behavior: Behavior, inputs: dict, client, destination: Path):
    """Text-only maintenance with a frozen behavior contract and a fresh output."""
    from .contracts import validate_bundle
    prompt = "Review this UI route as a text-only compiler. You must preserve the frozen behavior contract, every step, target and checkpoint exactly. You may improve summary and parameter declarations, without removing input coverage. Return a complete Route JSON. Schema: " + json.dumps(Route.model_json_schema()) + "\nRoute: " + route.model_dump_json() + "\nBehavior: " + behavior.model_dump_json()
    answer = Route.model_validate(client.complete_json(prompt))
    validate_bundle(answer, behavior, inputs)
    if answer.revision <= route.revision:
        raise PolicyError("compiled candidate must have a new revision")
    if destination.exists():
        raise PolicyError("candidate destination exists; choose a new file")
    write_json(destination, answer.model_dump())
    return answer


class OutcomeCheckpoint(Checkpoint):
    after_step: str


class OutcomeSpec(Strict):
    case_id: str
    original_intent: str
    oracle_status: Literal["confirmed", "pending"]
    targets: dict[str, Target] = Field(default_factory=dict)
    checkpoints: dict[str, OutcomeCheckpoint]
    excluded: list[str] = Field(default_factory=list)


def prepare_case(exploration: Path, outcome: OutcomeSpec, destination: Path):
    """Attach separately authored expected results; never infer success from done."""
    from .evidence import verify_integrity
    from .contracts import validate_bundle
    if verify_integrity(exploration):
        raise PolicyError("exploration evidence changed")
    state = json.loads((exploration / "exploration.json").read_text())
    if state["status"] != "candidate":
        raise PolicyError("exploration has no complete candidate")
    raw = json.loads((exploration / "candidate_route.json").read_text())
    if set(raw["targets"]) & set(outcome.targets):
        raise PolicyError("outcome cannot replace observed action targets")
    raw["case_id"] = outcome.case_id
    raw["targets"].update({k: v.model_dump() for k, v in outcome.targets.items()})
    used = set()
    for ref, cp in outcome.checkpoints.items():
        step = next((s for s in raw["steps"] if s["id"] == cp.after_step), None)
        if step is None or cp.after_step in used:
            raise PolicyError("outcome step missing or has multiple checkpoints")
        used.add(cp.after_step)
        step["checkpoint"] = ref
        raw["checkpoints"][ref] = cp.model_dump(exclude={"after_step"})
    if not raw["checkpoints"]:
        raise PolicyError("candidate needs independently supplied expected outcomes")
    route = Route.model_validate(raw)
    behavior = Behavior(case_id=route.case_id, revision=1, original_intent=outcome.original_intent, oracle_status=outcome.oracle_status, required_steps=route.steps, required_targets=route.targets, required_checkpoints=route.checkpoints, excluded=outcome.excluded)
    inputs = json.loads((exploration / "inputs.json").read_text())
    validate_bundle(route, behavior, inputs)
    destination.mkdir(parents=True, exist_ok=False)
    for file, value in [("route.json", route.model_dump()), ("behavior.json", behavior.model_dump()), ("environment.json", json.loads((exploration / "environment.json").read_text())), ("inputs.json", inputs)]:
        write_json(destination / file, value)
    write_json(destination / "provenance.json", {"exploration": str(exploration.resolve()), "source_integrity_sha256": digest_file(exploration / 'integrity.json'), "replay_verified": False})
    return route
