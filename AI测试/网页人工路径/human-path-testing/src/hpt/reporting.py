from __future__ import annotations
import json
from pathlib import Path
from .evidence import verify_integrity, write_json


def render_report(run: Path, r: dict):
    text = [f"# UI 路线运行：{r['overall']}", "", f"运行：`{r['run_id']}`；用例：`{r['case_id']}`。", "", "**结论范围：仅本次固定 Runner 的操作通道与声明检查；未认证整个主机隔离，也不代表完全人工等价。**", "", "| 维度 | 结果 |", "|---|---|"]
    for k in ["functional", "path", "visual", "evidence", "environment", "failure_category", "certification", "cleanup"]:
        text.append(f"| {k} | {r.get(k)} |")
    text += ["", f"完成 {len(r['completed_steps'])}/{len(r['expected_steps'])} 个动作；检查点断言另见 assertions.jsonl。", "", "## 错误或限制", "", "```text", r.get("error") or "没有记录到动作错误。", "```", ""]
    text += ["- " + x for x in r["limitations"]]
    text += ["", "## 本次截图", ""]
    for cp in json.loads((run / "checkpoints.json").read_text()):
        text += [f"### {cp['checkpoint_id']}", "", f"![{cp['checkpoint_id']}]({cp['screenshot']})", ""]
    text += ["## 证据", "", "route.json / behavior.json / environment.json / inputs.json / events.jsonl / assertions.jsonl / checkpoints.json / trace.zip / integrity.json。", "", "实际输入与原始截图可能含业务信息；共享前选择脱敏副本，不覆盖原始证据。"]
    (run / "report.md").write_text("\n".join(text), encoding="utf-8")


def compare_runs(old: Path, new: Path):
    a, b = [json.loads((x / "result.json").read_text()) for x in [old, new]]
    return {"old_run": old.name, "new_run": new.name, "first_result": a["overall"], "new_result": b["overall"], "recovered": a["overall"] != "PASS" and b["overall"] == "PASS", "same_case": a["case_id"] == b["case_id"], "integrity_issues": {old.name: verify_integrity(old), new.name: verify_integrity(new)}, "note": "Independent runs retained; later success does not replace original failure."}

