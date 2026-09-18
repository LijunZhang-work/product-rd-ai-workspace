"""Runner tests use an explicitly fake CLI. They do not validate CodeQL syntax."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "scripts/run_codeql.py"


class CodeQLAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fake-codeql-adapter-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "db"; self.db.mkdir()
        (self.db / "codeql-database.yml").write_text("# fake metadata for adapter tests only\n")
        self.queries = self.root / "queries"; self.queries.mkdir()
        (self.queries / "qlpack.yml").write_text("# fake pack for adapter tests only\n")
        (self.queries / "codeql-pack.lock.yml").write_text("# fake lock for adapter tests only\n")
        (self.queries / "Scope.qll").write_text("# adapter fixture; not QL\n")
        for name in ["Q00_Definitions.ql", "Q01_ExtractionErrors.ql"]:
            (self.queries / name).write_text("# adapter fixture; not QL\n")
        self.fake = self.root / "fake-codeql"
        self.fake.write_text("#!" + sys.executable + "\n" +
            "import sys\nfrom pathlib import Path\n"
            "args=sys.argv[1:]\n"
            "if args==['version']: print('FAKE CLI: adapter testing only')\n"
            "elif args[:2]==['query','run']:\n"
            " out=next(x.split('=',1)[1] for x in args if x.startswith('--output=')); Path(out).write_bytes(b'FAKE')\n"
            "elif args[:2]==['bqrs','decode']:\n"
            " out=Path(next(x.split('=',1)[1] for x in args if x.startswith('--output=')))\n"
            " mode=(Path(__file__).parent/'mode').read_text()\n"
            " count=(0 if mode=='empty' else 1) if 'Q00' in str(out) else (1 if mode=='error' else 0)\n"
            " out.write_text('file,function\\n'+('/fixture/source.cpp,entry\\n'*count))\n"
            "else: raise SystemExit(9)\n")
        self.fake.chmod(0o755)
        (self.root / "mode").write_text("ok")

    def run_adapter(self, executable=None):
        return subprocess.run([sys.executable, str(RUNNER), "--database", str(self.db), "--target", "adapter-fixture",
                               "--queries", str(self.queries), "--out", str(self.root / "out"),
                               "--codeql", str(executable or self.fake)], capture_output=True, text=True, timeout=30)

    def test_missing_executable_is_explicit(self):
        r = self.run_adapter(self.root / "missing-cli")
        self.assertEqual(r.returncode, 2); self.assertIn("not available", r.stderr)

    def test_placeholder_scope_is_rejected(self):
        (self.queries / "Scope.qll").write_text("__SET_PRODUCT_SCOPE__")
        r = self.run_adapter(); self.assertEqual(r.returncode, 2); self.assertIn("Scope.qll", r.stderr)

    def test_missing_lock_is_rejected(self):
        (self.queries / "codeql-pack.lock.yml").unlink()
        r = self.run_adapter(); self.assertEqual(r.returncode, 2); self.assertIn("pack lock", r.stderr)

    def test_fake_cli_records_do_not_claim_truth(self):
        r = self.run_adapter(); self.assertEqual(r.returncode, 0, r.stderr)
        summary = json.loads((self.root / "out/summary.json").read_text())
        self.assertIs(summary["semantic_truth_checked"], False)
        self.assertEqual(len(summary["queries"]), 2)
        self.assertTrue((self.root / "out/Q00_Definitions/query/run.json").is_file())

    def test_empty_definition_inventory_is_rejected(self):
        (self.root / "mode").write_text("empty")
        r = self.run_adapter(); self.assertEqual(r.returncode, 2)
        self.assertIn("empty/invalid", r.stdout)

    def test_extraction_errors_are_not_ignored(self):
        (self.root / "mode").write_text("error")
        r = self.run_adapter(); self.assertEqual(r.returncode, 2)
        self.assertIn("extraction errors", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
