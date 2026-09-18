#!/usr/bin/env python3
"""Execute the supplied inventory queries with the real local CodeQL CLI.
Does not install CodeQL, create a database, alter source, or infer missing IPC edges.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys

import probe


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--codeql", default="codeql")
    p.add_argument("--timeout", type=float, default=1800)
    p.add_argument("--queries", default=str(Path(__file__).resolve().parents[1] / "queries/codeql"))
    a = p.parse_args()
    try:
        executable = shutil.which(a.codeql)
        if not executable:
            raise ValueError("CodeQL not available; record a gap and continue other tools")
        database = Path(a.database).resolve()
        db_meta = database / "codeql-database.yml"
        if not db_meta.is_file():
            raise ValueError("Not a resolved CodeQL database: missing codeql-database.yml")
        query_dir = Path(a.queries).resolve()
        scope = query_dir / "Scope.qll"
        if "__SET_" in scope.read_text(encoding="utf-8"):
            raise ValueError("Set and review Scope.qll before querying")
        lock = query_dir / "codeql-pack.lock.yml"
        if not lock.is_file():
            raise ValueError("Missing pack lock; resolve approved codeql/cpp-all dependency and preserve its lock")
        queries = sorted(query_dir.glob("Q*.ql"))
        if not queries or not any(q.name == "Q00_Definitions.ql" for q in queries):
            raise ValueError("Query inventory missing Q00_Definitions.ql")
        out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=False)
        rows, errors = [], []
        version = probe.record_command(out / "version", query_dir, [executable, "version"], a.target, [], 30)
        if version["status"] != "succeeded":
            raise ValueError("CodeQL version command failed; see recorded output")
        for q in queries:
            base = out / q.stem; base.mkdir()
            result = base / "result.bqrs"
            inputs = [str(q), str(scope), str(lock), str(query_dir / "qlpack.yml"), str(db_meta)]
            run = probe.record_command(base / "query", query_dir,
                                       [executable, "query", "run", "--database=" + str(database),
                                        "--output=" + str(result), str(q)], a.target, inputs, a.timeout)
            row = {"query": q.name, "execution": run["status"]}
            if run["status"] != "succeeded" or not result.is_file():
                errors.append(q.name + ": query failed or result missing")
                rows.append(row)
                continue
            csv_path = base / "result.csv"
            decode = probe.record_command(base / "decode", query_dir,
                                          [executable, "bqrs", "decode", "--format=csv", "--output=" + str(csv_path), str(result)],
                                          a.target, [str(result)], a.timeout)
            row["decode"] = decode["status"]
            if decode["status"] != "succeeded" or not csv_path.is_file():
                errors.append(q.name + ": decode failed or CSV missing")
            else:
                with csv_path.open(encoding="utf-8-sig", newline="") as f:
                    reader = csv.DictReader(f)
                    row["columns"] = reader.fieldnames
                    row["rows"] = sum(1 for _ in reader)
                row["csv_sha256"] = probe.sha(csv_path)
                if q.name == "Q00_Definitions.ql" and (row["rows"] == 0 or "file" not in (row["columns"] or [])):
                    errors.append("Q00 definition inventory empty/invalid: scope or extraction must be checked")
                if q.name == "Q01_ExtractionErrors.ql" and row["rows"]:
                    errors.append("Q01 found function extraction errors: affected conclusions require repair or explicit gaps")
            rows.append(row)
        report = probe.report("codeql_inventory_run", errors, target=a.target,
                              database=str(database), database_metadata_sha256=probe.sha(db_meta),
                              queries=rows, semantic_truth_checked=False,
                              meaning="Queries were executed; rows remain static candidates requiring review")
        probe.write_json(out / "summary.json", report)
        print(json.dumps({"summary": str(out / "summary.json"), "errors": errors}, ensure_ascii=False))
        return 2 if errors else 0
    except (ValueError, OSError, TypeError) as e:
        print("ERROR: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
