"""Regression and host-tool checks; these do not validate a real product target."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "probe.py"
spec = importlib.util.spec_from_file_location("probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fact-probe-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.product = self.root / "product"
        self.emap = self.root / "emap"
        self.product.mkdir(); self.emap.mkdir()
        self.a = self.product / "main.cpp"
        self.b = self.emap / "backend.cpp"
        self.a.write_text("int entry() { return 1; }\n")
        self.b.write_text("int backend() { return 2; }\n")
        self.repos = {"product": str(self.product), "emap": str(self.emap)}
        self.db = self.root / "compile_commands.json"
        self.commands = [dict(directory=str(p.parent), file=p.name,
                              arguments=["g++", "-DREAL_TARGET=1", "-c", p.name]) for p in (self.a, self.b)]
        self.db.write_text(json.dumps(self.commands))

    def audit(self, commands=None, keys=None):
        if commands is not None:
            self.db.write_text(json.dumps(commands))
        return probe.audit_compdb(self.db, self.repos, keys if keys is not None else [str(self.a), str(self.b)])

    def ledger(self):
        evidence = self.root / "source.txt"
        evidence.write_text("int entry() { return 1; }\n")
        return {"schema_version": 1, "baselines": {"p1": {"commit": "fixture"}},
                "targets": ["t1", "t2"],
                "evidence": [{"id": "E1", "kind": "S", "baseline_id": "p1", "targets": ["t1"],
                              "path": "source.txt", "sha256": probe.sha(evidence),
                              "supports": "fixture source exists", "limitations": "no linked product"}],
                "claims": [{"id": "C1", "status": "verified", "scope": "source", "target": "t1",
                            "baseline_ids": ["p1"], "text": "source contains entry", "evidence_ids": ["E1"],
                            "limitations": "source only", "review_note": "read fixture source"}]}

    def test_compdb_both_repositories(self):
        r = self.audit()
        self.assertFalse(r["errors"])
        self.assertEqual(r["repository_source_counts"], {"product": 1, "emap": 1})

    def test_missing_emap_key_is_error(self):
        r = self.audit(self.commands[:1])
        self.assertTrue(any("not captured" in x for x in r["errors"]))

    def test_multi_variant_is_not_silently_deduplicated(self):
        other = copy.deepcopy(self.commands[0]); other["arguments"][1] = "-DREAL_TARGET=2"
        r = self.audit(self.commands + [other])
        self.assertEqual(r["entry_count"], 3)
        self.assertEqual(r["multi_command_sources"][str(self.a)], 2)

    def test_command_with_spaces(self):
        p = self.product / "a file.cpp"; p.write_text("int x;\n")
        r = self.audit([dict(directory=str(self.product), file=p.name, command="g++ -c 'a file.cpp'")], [str(p)])
        self.assertFalse(r["errors"])
        self.assertEqual(r["entries"][0]["arguments"][-1], "a file.cpp")

    def test_response_file_missing(self):
        self.commands[0]["arguments"].append("@missing.rsp")
        self.assertTrue(any("response file missing" in x for x in self.audit(self.commands)["errors"]))

    def test_compdb_does_not_execute_commands(self):
        marker = self.root / "bad"
        self.commands[0]["arguments"] = [sys.executable, "-c", f"open({str(marker)!r}, 'w').write('bad')"]
        before = probe.sha(self.a)
        self.audit(self.commands)
        self.assertFalse(marker.exists())
        self.assertEqual(before, probe.sha(self.a))

    def test_empty_database_is_error(self):
        self.assertTrue(self.audit([])["errors"])

    def test_overlapping_roots_are_error(self):
        self.repos["emap"] = str(self.product / "nested")
        self.assertTrue(any("overlapping" in x for x in self.audit()["errors"]))

    def test_definition_presence_missing_backend(self):
        report = self.root / "compdb.json"; probe.write_json(report, self.audit())
        csvfile = self.root / "defs.csv"
        with csvfile.open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["file", "function"]); w.writerow([self.a, "entry"])
        r = probe.compare_definitions(report, csvfile, [str(self.b)], [])
        self.assertTrue(r["errors"])
        self.assertIn(str(self.b), r["missing_definition_files"])

    def test_definition_prefix_mapping_is_recorded(self):
        report = self.root / "compdb.json"; probe.write_json(report, self.audit())
        csvfile = self.root / "defs.csv"
        csvfile.write_text("file,function\n/old/product/main.cpp,entry\n/old/emap/backend.cpp,backend\n")
        r = probe.compare_definitions(report, csvfile, [str(self.b)], ["/old=" + str(self.root)])
        self.assertFalse(r["errors"])
        self.assertTrue(r["prefix_maps"])

    def test_valid_ledger_is_mechanical_only(self):
        r = probe.validate_ledger(self.ledger(), self.root)
        self.assertFalse(r["errors"])
        self.assertIs(r["semantic_truth_checked"], False)

    def test_corrupt_evidence_detected(self):
        ledger = self.ledger(); (self.root / "source.txt").write_text("changed")
        self.assertTrue(any("digest mismatch" in x for x in probe.validate_ledger(ledger, self.root)["errors"]))

    def test_unknown_evidence_detected(self):
        ledger = self.ledger(); ledger["claims"][0]["evidence_ids"] = ["E404"]
        self.assertTrue(probe.validate_ledger(ledger, self.root)["errors"])

    def test_wrong_target_detected(self):
        ledger = self.ledger(); ledger["claims"][0]["target"] = "t2"
        self.assertTrue(any("target mismatch" in x for x in probe.validate_ledger(ledger, self.root)["errors"]))

    def test_wrong_baseline_detected(self):
        ledger = self.ledger(); ledger["baselines"]["p2"] = {"commit": "other"}
        ledger["claims"][0]["baseline_ids"] = ["p2"]
        self.assertTrue(any("baseline mismatch" in x for x in probe.validate_ledger(ledger, self.root)["errors"]))

    def test_source_cannot_be_promoted_to_running(self):
        ledger = self.ledger(); ledger["claims"][0]["scope"] = "running"
        self.assertTrue(any("missing evidence kinds" in x for x in probe.validate_ledger(ledger, self.root)["errors"]))

    def test_evidence_path_escape_detected(self):
        ledger = self.ledger(); ledger["evidence"][0]["path"] = "../outside.txt"
        self.assertTrue(probe.validate_ledger(ledger, self.root)["errors"])

    def test_symlink_escape_detected(self):
        ledger = self.ledger()
        with tempfile.TemporaryDirectory() as outside:
            other = Path(outside) / "other"; other.write_text("outside")
            link = self.root / "link"; link.symlink_to(other)
            ledger["evidence"][0].update(path="link", sha256=probe.sha(other))
            self.assertTrue(probe.validate_ledger(ledger, self.root)["errors"])

    def test_unknown_is_retained_as_gap(self):
        ledger = self.ledger()
        ledger["claims"][0].update(status="unknown", evidence_ids=[], gap="G1", next_action="obtain link map")
        r = probe.validate_ledger(ledger, self.root)
        self.assertFalse(r["errors"])
        self.assertEqual(r["unresolved_claims"], ["C1"])

    def test_record_preserves_literal_arguments(self):
        arg = "$(do-not-run); a b"
        r = probe.record_command(self.root / "run", self.root,
                                 [sys.executable, "-c", "import sys; print(sys.argv[1])", arg], "fixture", [], 10)
        self.assertEqual(r["status"], "succeeded")
        self.assertEqual((self.root / "run/stdout.txt").read_text().strip(), arg)

    def test_record_nonzero_is_failure(self):
        r = probe.record_command(self.root / "run", self.root, [sys.executable, "-c", "raise SystemExit(7)"], "fixture", [], 10)
        self.assertEqual(r["exit_code"], 7)
        self.assertEqual(r["status"], "failed")

    def test_record_timeout(self):
        r = probe.record_command(self.root / "run", self.root, [sys.executable, "-c", "import time; time.sleep(10)"], "fixture", [], .05)
        self.assertEqual(r["status"], "timed_out")

    def test_record_changed_input_is_failure(self):
        r = probe.record_command(self.root / "run", self.root,
                                 [sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('changed')", str(self.a)],
                                 "fixture", [str(self.a)], 10)
        self.assertEqual(r["status"], "inputs_changed")

    def test_record_never_overwrites_run(self):
        out = self.root / "run"; out.mkdir(); (out / "keep").write_text("keep")
        with self.assertRaises(FileExistsError):
            probe.record_command(out, self.root, [sys.executable, "--version"], "fixture", [], 10)
        self.assertEqual((out / "keep").read_text(), "keep")

    def test_report_never_overwrites(self):
        out = self.root / "result.json"; probe.write_json(out, {"keep": 1})
        with self.assertRaises(FileExistsError):
            probe.write_json(out, {"keep": 2})
        self.assertEqual(probe.read_json(out), {"keep": 1})

    @unittest.skipUnless(shutil.which("gcc") and shutil.which("nm") and shutil.which("readelf"), "host GCC/Binutils unavailable")
    def test_real_host_macros_and_linked_backend(self):
        source = self.root / "fixture.c"
        source.write_text("#ifdef REAL_BACKEND\nint backend_real(void){return 1;}\n#define selected backend_real\n#else\nint backend_dt(void){return 2;}\n#define selected backend_dt\n#endif\nint main(void){return selected();}\n")
        for variant, flag, expected, absent in [("real", "-DREAL_BACKEND", "backend_real", "backend_dt"),
                                                 ("dt", "-UREAL_BACKEND", "backend_dt", "backend_real")]:
            binary = self.root / (variant + ".elf")
            build = probe.record_command(self.root / (variant + "-build"), self.root,
                                         [shutil.which("gcc"), "-g", "-O0", flag, str(source),
                                          "-Wl,-Map=" + str(self.root / (variant + ".map")), "-o", str(binary)],
                                         "host-fixture-" + variant, [str(source)], 30)
            self.assertEqual(build["status"], "succeeded")
            symbols = subprocess.run(["nm", "--defined-only", str(binary)], check=True, capture_output=True, text=True).stdout
            self.assertIn(expected, symbols); self.assertNotIn(absent, symbols)
            headers = subprocess.run(["readelf", "--file-header", str(binary)], check=True, capture_output=True, text=True).stdout
            self.assertIn("ELF", headers)
            self.assertTrue((self.root / (variant + ".map")).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
