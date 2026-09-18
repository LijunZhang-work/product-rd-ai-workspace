"""Regression checks for omission detection; fixtures are not product evidence."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("workflow", Path(__file__).resolve().parents[1] / "scripts/check_workflow.py")
workflow = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "fixture-evidence.txt").write_text("Synthetic coverage fixture, not a tool execution result.")
        self.manifest = workflow.read_json(workflow.MANIFEST)
        self.state = workflow.initial_state(self.manifest, "full", ["build_a", "build_b"])
        self.state["tool_report_reference"] = "fixture-evidence.txt"
        for task in self.state["tasks"]:
            task.update(status="completed", evidence=["fixture-evidence.txt"])
            if task["step_id"] in workflow.TOOL_RUN_STEPS:
                task["task_run_evidence"] = ["fixture-evidence.txt"]

    def check(self, state=None):
        return workflow.check_state(self.manifest, state or self.state, self.root, "full")

    def test_complete_declarations_are_not_semantic_proof(self):
        report = self.check()
        self.assertEqual(report["errors"], [])
        self.assertFalse(report["semantic_truth_checked"])
        self.assertFalse(report["tool_execution_checked"])
        self.assertFalse(report["tool_readiness_checked"])

    def test_installation_evidence_cannot_omit_task_run_reference(self):
        task = next(t for t in self.state["tasks"] if t["step_id"] == "S07")
        del task["task_run_evidence"]
        self.assertTrue(any("installation alone" in e for e in self.check()["errors"]))

    def test_current_tool_report_reference_is_required(self):
        del self.state["tool_report_reference"]
        self.assertTrue(any("tool_report_reference" in e for e in self.check()["errors"]))

    def test_task_run_reference_must_exist(self):
        task = next(t for t in self.state["tasks"] if t["step_id"] == "S06")
        task["task_run_evidence"] = ["missing-run.json"]
        self.assertTrue(any("task_run_evidence" in e for e in self.check()["errors"]))

    def test_missing_configuration_step_is_detected(self):
        self.state["tasks"] = [t for t in self.state["tasks"] if (t["step_id"], t["scope"]) != ("S07", "build_b")]
        self.assertIn("S07/build_b: missing task", self.check()["errors"])

    def test_required_step_cannot_be_marked_inapplicable(self):
        self.state["tasks"][0].update(status="not_applicable", reason="skip")
        self.assertTrue(any("cannot be skipped" in e for e in self.check()["errors"]))

    def test_optional_choice_requires_reason_and_evidence(self):
        task = next(t for t in self.state["tasks"] if t["step_id"] == "S12")
        task.update(status="not_applicable", reason="", evidence=[])
        errors = self.check()["errors"]
        self.assertTrue(any("reason required" in e for e in errors))
        self.assertTrue(any("evidence required" in e for e in errors))
        task.update(reason="Not selected for this scope", evidence=["fixture-evidence.txt"])
        self.assertEqual(self.check()["errors"], [])

    def test_pending_partial_blocked_are_not_complete(self):
        for status in ("pending", "partial", "blocked"):
            with self.subTest(status=status):
                state = copy.deepcopy(self.state)
                state["tasks"][0].update(status=status, reason="waiting")
                self.assertFalse(self.check(state)["workflow_records_complete"])

    def test_missing_and_empty_evidence_are_detected(self):
        (self.root / "empty").touch()
        for name in ("absent", "empty"):
            with self.subTest(name=name):
                state = copy.deepcopy(self.state)
                state["tasks"][0]["evidence"] = [name]
                self.assertTrue(self.check(state)["errors"])

    def test_outside_evidence_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            p = Path(outside) / "evidence"
            p.write_text("outside")
            (self.root / "escape").symlink_to(p)
            self.state["tasks"][0]["evidence"] = ["escape"]
            self.assertTrue(any("out-of-root" in e for e in self.check()["errors"]))

    def test_duplicate_task_and_manifest_drift_are_detected(self):
        self.state["tasks"].append(copy.deepcopy(self.state["tasks"][0]))
        self.state["manifest_sha256"] = "wrong"
        errors = self.check()["errors"]
        self.assertTrue(any("duplicate task" in e for e in errors))
        self.assertTrue(any("manifest" in e for e in errors))

    def test_full_mode_cannot_silently_become_preparation(self):
        state = workflow.initial_state(self.manifest, "preparation", [])
        for task in state["tasks"]:
            task.update(status="completed", evidence=["fixture-evidence.txt"])
        report = workflow.check_state(self.manifest, state, self.root, "full")
        self.assertIn("Declared scope differs from requested scope", report["errors"])

    def test_reuse_requires_applicability_reason(self):
        self.state["tasks"][0].update(status="reused", reason="")
        self.assertTrue(any("reason required" in e for e in self.check()["errors"]))

    def test_package_missing_payload_and_unreachable_document(self):
        (self.root / "00.md").write_text("[guide](guide.md)")
        (self.root / "guide.md").write_text("[missing](missing.py)")
        (self.root / "orphan.md").write_text("orphan")
        manifest = {"entry": "00.md", "required_files": ["00.md", "scripts/tool.py"]}
        errors = workflow.check_package(self.root, manifest)["errors"]
        self.assertTrue(any("required" in e for e in errors))
        self.assertTrue(any("Broken" in e for e in errors))
        self.assertTrue(any("unreachable" in e for e in errors))

    def shared_package(self):
        workspace = self.root / "workspace"
        kit = workspace / "产品与EMAP事实探查" / "成熟工具增强事实探查"
        kit.mkdir(parents=True)
        shared = workspace / "工具接入与共享能力"
        shared.mkdir()
        names = sorted(workflow.SHARED_DEPENDENCIES)
        (kit / "00.md").write_text("\n".join("[shared](" + n + ")" for n in names))
        for name in names:
            (shared / Path(name).name).write_text("尚未盘点，真实工具状态未知。")
        manifest = {"version": "1.2", "entry": "00.md", "required_files": ["00.md"],
                    "shared_dependencies": names}
        return kit, shared, manifest

    def test_shared_guide_and_unknown_report_only_prove_package_complete(self):
        kit, _, manifest = self.shared_package()
        report = workflow.check_package(kit, manifest)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["shared_documents"], 2)
        self.assertFalse(report["tool_readiness_checked"])
        self.assertFalse(report["tool_execution_checked"])

    def test_missing_shared_guide_is_detected(self):
        kit, shared, manifest = self.shared_package()
        (shared / "工具统一管理与使用指南.md").unlink()
        self.assertTrue(any("shared dependency" in e for e in workflow.check_package(kit, manifest)["errors"]))

    def test_empty_shared_report_is_detected(self):
        kit, shared, manifest = self.shared_package()
        (shared / "工具状态与验收报告.md").write_text("")
        self.assertTrue(any("shared dependency" in e for e in workflow.check_package(kit, manifest)["errors"]))

    def test_shared_dependency_cannot_escape_allowlist(self):
        kit, _, manifest = self.shared_package()
        manifest["shared_dependencies"].append("../../../outside.md")
        self.assertTrue(any("Disallowed shared" in e for e in workflow.check_package(kit, manifest)["errors"]))

    def test_shared_dependency_symlink_cannot_escape_expected_location(self):
        kit, shared, manifest = self.shared_package()
        outside = self.root / "outside.md"
        outside.write_text("outside")
        guide = shared / "工具统一管理与使用指南.md"
        guide.unlink()
        guide.symlink_to(outside)
        self.assertTrue(any("out-of-location" in e for e in workflow.check_package(kit, manifest)["errors"]))

    def test_v12_manifest_cannot_drop_shared_dependencies(self):
        kit, _, manifest = self.shared_package()
        del manifest["shared_dependencies"]
        self.assertTrue(any("declarations" in e for e in workflow.check_package(kit, manifest)["errors"]))

    def test_existing_progress_file_is_not_overwritten(self):
        path = self.root / "state.json"
        path.write_text("keep existing progress")
        code = workflow.main(["init", "--mode", "preparation", "--out", str(path)])
        self.assertEqual(code, 2)
        self.assertEqual(path.read_text(), "keep existing progress")


if __name__ == "__main__":
    unittest.main()
