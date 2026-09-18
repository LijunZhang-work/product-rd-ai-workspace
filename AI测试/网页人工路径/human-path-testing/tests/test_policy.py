import copy
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from hpt.contracts import Route, Environment, PolicyError, validate_bundle
from hpt.examples import make_case, CASE_NAMES
from hpt.runner import summarize
from hpt.evidence import new_run, write_json, seal, verify_integrity
from hpt.vision import validate_answer, import_review


@pytest.mark.parametrize("name", CASE_NAMES)
def test_all_authored_cases_satisfy_independent_contract(name):
    route, behavior, _, inputs = make_case(name)
    validate_bundle(route, behavior, inputs)


@pytest.mark.parametrize("action", ["http_request", "evaluate", "dispatch_event", "storage_write", "mock", "shell", "custom_action"])
def test_business_shortcuts_are_unrepresentable(action):
    route, *_ = make_case()
    raw = route.model_dump()
    raw["steps"][2]["action"] = action
    with pytest.raises(ValidationError):
        Route.model_validate(raw)


@pytest.mark.parametrize("field,value", [("force", True), ("script", "fetch('/devices')"), ("url", "http://127.0.0.1/result"), ("headers", {}), ("method", "POST")])
def test_unknown_nested_fields_rejected(field, value):
    route, *_ = make_case()
    raw = route.model_dump()
    raw["steps"][2][field] = value
    with pytest.raises(ValidationError):
        Route.model_validate(raw)


@pytest.mark.parametrize("mutation", ["second_entry", "missing_checkpoint", "cycle", "bool_timeout", "duplicate_step", "path_id"])
def test_structure_failures(mutation):
    route, *_ = make_case()
    raw = route.model_dump()
    if mutation == "second_entry":
        raw["steps"].append({"id": "S99", "business_id": "bad", "action": "open_entry"})
    elif mutation == "missing_checkpoint":
        raw["steps"][-1]["checkpoint"] = None
    elif mutation == "cycle":
        raw["targets"]["dialog"]["scope"] = "name"
    elif mutation == "bool_timeout":
        raw["steps"][0]["timeout_ms"] = True
    elif mutation == "duplicate_step":
        raw["steps"][-1]["id"] = "S01"
    else:
        raw["case_id"] = ".."
    with pytest.raises(ValidationError):
        Route.model_validate(raw)


@pytest.mark.parametrize("mutation", ["delete_step", "weaken_assertion", "rename_target"])
def test_frozen_behavior_detects_semantic_drift(mutation):
    route, behavior, _, inputs = make_case()
    raw = route.model_dump()
    if mutation == "delete_step":
        raw["steps"].pop(3)
    elif mutation == "weaken_assertion":
        raw["checkpoints"]["CP_PERSISTED"]["assertions"] = [{"target": "heading", "kind": "visible"}]
    else:
        raw["targets"]["save"]["name"] = "Bypass save"
    changed = Route.model_validate(raw)
    with pytest.raises(PolicyError):
        validate_bundle(changed, behavior, inputs)


@pytest.mark.parametrize("value", [42, True, "", "a" * 33])
def test_inputs_are_strict(value):
    route, behavior, _, inputs = make_case()
    inputs["device_name"] = value
    with pytest.raises(PolicyError):
        validate_bundle(route, behavior, inputs)


@pytest.mark.parametrize("url", ["javascript:alert(1)", "file:///tmp/test", "https://user:pass@example.org", "https://other.test/"])
def test_entry_boundary(url):
    with pytest.raises(ValidationError):
        Environment(name="bad", entry_url=url, allowed_origins=["https://example.org"])


@pytest.mark.parametrize("state,expected", [
    (("pass", "pass", "pass", "complete", "ready", None), "PASS"),
    (("pass", "pass", "not_checked", "complete", "ready", None), "INCOMPLETE"),
    (("pass", "pass", "uncertain", "complete", "ready", None), "INCOMPLETE"),
    (("pass", "pass", "pass", "incomplete", "ready", None), "INCOMPLETE"),
    (("fail", "unknown", "not_checked", "incomplete", "ready", None), "FAIL"),
    (("not_run", "unknown", "not_checked", "incomplete", "blocked", "ENVIRONMENT"), "BLOCKED"),
    (("not_run", "unknown", "not_checked", "incomplete", "ready", "UNSUPPORTED"), "UNSUPPORTED"),
])
def test_result_gates(state, expected):
    assert summarize(*state) == expected


def test_evidence_missing_changed_and_added_files_are_detected(tmp_path):
    run = new_run(tmp_path)
    write_json(run / "result.json", {"status": "original"})
    seal(run)
    assert verify_integrity(run) == []
    write_json(run / "result.json", {"status": "forged"})
    assert "result.json" in verify_integrity(run)
    (run / "result.json").unlink()
    assert "result.json" in verify_integrity(run)


def test_visual_cannot_omit_required_check():
    with pytest.raises(PolicyError):
        validate_answer({"checks": [{"item": "A", "status": "pass", "reason": "Visible"}]}, ["A", "B"])


def test_visual_cannot_invent_status():
    with pytest.raises(ValidationError):
        validate_answer({"checks": [{"item": "A", "status": "probably", "reason": "Looks good"}]}, ["A"])

