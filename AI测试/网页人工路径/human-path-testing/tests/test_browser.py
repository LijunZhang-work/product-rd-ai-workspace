"""Real browser integration. No mocked browser, DOM, or app success responses."""
import json
import os
from pathlib import Path
import pytest

from hpt.examples import make_case, seed_case, CASE_NAMES
from hpt.fixture import serve_fixture
from hpt.runner import execute
from hpt.evidence import verify_integrity
from hpt.registry import publish, recommend
from hpt.contracts import PolicyError
from hpt.vision import import_review

pytestmark = pytest.mark.browser


def evidence_root(tmp_path):
    return Path(os.environ.get("HPT_TEST_ARTIFACTS", str(tmp_path)))


@pytest.mark.parametrize("iteration", [1, 2, 3])
@pytest.mark.parametrize("name", CASE_NAMES)
def test_ten_scenarios_three_clean_replays(name, iteration, tmp_path):
    with serve_fixture() as (fixture, url):
        route, behavior, env, inputs = make_case(name, url, visual=False)
        seed_case(fixture, name, inputs)
        folder, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "regression")
        assert result["overall"] == "PASS", result
        assert result["certification"] == "INCOMPLETE"
        assert result["visual"] == "not_required"
        assert verify_integrity(folder) == []
        events = [json.loads(s) for s in (folder / "events.jsonl").read_text().splitlines()]
        assert len([e for e in events if e["type"] == "action_finished"]) == len(route.steps)
        assert [e["seq"] for e in events] == list(range(1, len(events)+1))
        diagnostics = [json.loads(s) for s in (folder / "diagnostics.jsonl").read_text().splitlines()]
        assert not [e for e in diagnostics if e["type"] == "pageerror"]
        if name not in {"duplicate"}:
            assert not [e for e in diagnostics if e["type"] == "response" and e["status"] >= 400]


@pytest.mark.parametrize("mode", ["overlay", "invisible", "http500", "no_persist", "wrong_type", "duplicate_button", "delayed_commit", "keyboard_only"])
def test_injected_fault_is_detected_without_shortcuts(mode, tmp_path):
    with serve_fixture(mode) as (fixture, url):
        route, behavior, env, inputs = make_case("create", url, visual=False)
        folder, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "faults")
        assert result["overall"] == "FAIL", result
        assert result["functional"] == "fail"
        assert verify_integrity(folder) == []
        assert fixture.write_count <= 1, "submissions must not be retried"
        if mode in {"overlay", "invisible", "duplicate_button"}:
            assert fixture.rows() == [], "blocked UI must not create data by another channel"
        if mode == "no_persist":
            assert "S09" in result["completed_steps"], "must reach real reload before proving persistence failure"


def test_missing_visual_provider_never_becomes_success(tmp_path):
    with serve_fixture() as (_, url):
        route, behavior, env, inputs = make_case(base_url=url, visual=True)
        folder, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "visual_required")
        assert result["functional"] == "pass"
        assert result["visual"] == "not_checked"
        assert result["overall"] == "INCOMPLETE"


def test_pending_oracle_blocks_pass(tmp_path):
    with serve_fixture() as (_, url):
        route, behavior, env, inputs = make_case(base_url=url, visual=False)
        behavior.oracle_status = "pending"
        _, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "pending")
        assert result["overall"] == "INCOMPLETE"


def test_keyboard_profile_exercises_real_key_events(tmp_path):
    with serve_fixture("keyboard_only") as (_, url):
        route, behavior, env, inputs = make_case("keyboard", url, visual=False)
        _, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "keyboard")
        assert result["overall"] == "PASS", result


def test_duplicate_backend_state_is_not_fresh_run_success(tmp_path):
    with serve_fixture() as (fixture, url):
        route, behavior, env, inputs = make_case(base_url=url, visual=False)
        fixture.seed(inputs["device_name"])
        _, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "dirty")
        assert result["overall"] == "FAIL"
        assert fixture.write_count == 0


def test_failed_cleanup_is_not_hidden(tmp_path):
    with serve_fixture("cleanup_fail") as (fixture, url):
        route, behavior, env, inputs = make_case("delete", url, visual=False)
        seed_case(fixture, "delete", inputs)
        _, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "cleanup")
        assert result["overall"] == "FAIL"
        assert len(fixture.rows()) == 1


def test_registry_rejects_overwrite_and_requires_old_inputs(tmp_path):
    with serve_fixture() as (_, url):
        route, behavior, env, inputs = make_case(base_url=url, visual=False)
        run, result = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "registry")
        assert result["overall"] == "PASS"
        registry = tmp_path / "registry"
        publish(registry, route, behavior, [run])
        assert recommend(registry, route.case_id, inputs)["verdict"] == "run"
        assert recommend(registry, route.case_id, {**inputs, "device_name": "New"})["verdict"] == "adapt"
        with pytest.raises(PolicyError):
            publish(registry, route, behavior, [run])
        route.revision = 2
        with pytest.raises(PolicyError):
            publish(registry, route, behavior, [run])


def test_external_review_binds_images_and_preserves_original(tmp_path):
    with serve_fixture() as (_, url):
        route, behavior, env, inputs = make_case(base_url=url, visual=True)
        run, _ = execute(route, behavior, env, inputs, evidence_root(tmp_path) / "review_protocol")
    # This is a protocol test, NOT an actual visual inspection. Always uncertain.
    review = {"reviewer": "protocol-test-not-a-visual-review", "method": "external_multimodal", "checkpoints": {}}
    for cp in json.loads((run / "checkpoints.json").read_text()):
        if cp["required_items"]:
            review["checkpoints"][cp["checkpoint_id"]] = {"sha256": cp["sha256"], "checks": [{"item": i, "status": "uncertain", "reason": "Protocol test does not inspect pixels"} for i in cp["required_items"]]}
    original = (run / "result.json").read_bytes()
    _, assessment = import_review(run, review, tmp_path / "assessments")
    assert assessment["assessed_ui_result"] == "INCOMPLETE"
    assert (run / "result.json").read_bytes() == original
    key = next(iter(review["checkpoints"]))
    review["checkpoints"][key]["sha256"] = "forged"
    with pytest.raises(PolicyError):
        import_review(run, review, tmp_path / "assessments")


def test_screenshot_lost_before_verdict_blocks_pass(tmp_path, monkeypatch):
    from hpt.runner import Driver
    original_close = Driver.close
    def remove_evidence(self):
        errors = original_close(self)
        if self.checkpoint_evidence:
            (self.run / self.checkpoint_evidence[-1]['screenshot']).unlink()
        return errors
    monkeypatch.setattr(Driver, 'close', remove_evidence)
    with serve_fixture() as (_, url):
        r, b, e, i = make_case(base_url=url, visual=False)
        _, result = execute(r, b, e, i, evidence_root(tmp_path) / 'missing-evidence')
        assert result['functional'] == 'pass'
        assert result['evidence'] == 'incomplete'
        assert result['overall'] == 'INCOMPLETE'


def test_runner_identity_change_is_not_accepted(tmp_path, monkeypatch):
    import hpt.runner as module
    original = module.runner_identity
    calls = 0
    def changed_identity():
        nonlocal calls
        calls += 1
        value = original()
        if calls > 1:
            value['simulated-changed-module.py'] = 'different'
        return value
    monkeypatch.setattr(module, 'runner_identity', changed_identity)
    with serve_fixture() as (fixture, url):
        r, b, e, i = make_case(base_url=url, visual=False)
        _, result = execute(r, b, e, i, evidence_root(tmp_path) / 'source-change')
        assert result['path'] == 'fail'
        assert result['overall'] == 'FAIL'
        assert fixture.write_count == 0
