from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import Field
from .contracts import Strict, PolicyError
from .evidence import Journal, digest_file, verify_integrity, new_run, write_json, seal


class VisualItem(Strict):
    item: str
    status: Literal["pass", "fail", "uncertain"]
    reason: str = Field(min_length=1, max_length=2000)


class VisualAnswer(Strict):
    checks: list[VisualItem] = Field(min_length=1, max_length=30)


def validate_answer(answer, required):
    parsed = VisualAnswer.model_validate(answer)
    if [c.item for c in parsed.checks] != required:
        raise PolicyError("visual answer must cover each required item exactly once, in order")
    return parsed


def aggregate(statuses):
    if "fail" in statuses:
        return "fail"
    if not statuses or any(s != "pass" for s in statuses):
        return "uncertain"
    return "pass"


def check_images(run: Path, checkpoints: list, client):
    journal = Journal(run / "visual_checks.jsonl")
    statuses = []
    for cp in checkpoints:
        try:
            shot = run / cp["screenshot"]
            if digest_file(shot) != cp["sha256"]:
                raise PolicyError("screenshot checksum mismatch")
            prompt = "Inspect only the attached screenshot. If pixels cannot establish an item, return uncertain. Do not infer success from the instructions. Return {\"checks\":[{\"item\":<exact item>,\"status\":\"pass|fail|uncertain\",\"reason\":<visible evidence>}]} for these ordered items: " + json.dumps(cp["required_items"], ensure_ascii=False)
            answer = validate_answer(client.complete_json(prompt, shot), cp["required_items"])
            status = aggregate([c.status for c in answer.checks])
            journal.append({"checkpoint_id": cp["checkpoint_id"], "screenshot_sha256": cp["sha256"], "status": status, "answer": answer.model_dump(), "receipt": client.last_receipt})
        except Exception as e:
            status = "uncertain"
            journal.append({"checkpoint_id": cp["checkpoint_id"], "status": status, "error": str(e)[:1500]})
        statuses.append(status)
    journal.finalize()
    return aggregate(statuses)


def import_review(source_run: Path, review: dict, output: Path):
    """A new assessment, not an overwrite of the immutable original run.

    Manual/external reviews are attestations, not cryptographically authenticated.
    The report explicitly retains this limitation.
    """
    issues = verify_integrity(source_run)
    if issues:
        raise PolicyError("source evidence has changed: " + str(issues))
    if set(review) != {"reviewer", "method", "checkpoints"} or review["method"] not in {"human", "external_multimodal"}:
        raise PolicyError("review requires reviewer, method and checkpoints")
    if not isinstance(review["reviewer"], str) or not review["reviewer"].strip():
        raise PolicyError("reviewer is missing")
    required = {c["checkpoint_id"]: c for c in json.loads((source_run / "checkpoints.json").read_text()) if c["required_items"]}
    if set(review["checkpoints"]) != set(required):
        raise PolicyError("review checkpoint coverage differs from required set")
    statuses = []
    for ref, cp in required.items():
        r = review["checkpoints"][ref]
        if set(r) != {"sha256", "checks"} or r["sha256"] != cp["sha256"]:
            raise PolicyError("review image binding mismatch")
        answer = validate_answer({"checks": r["checks"]}, cp["required_items"])
        statuses.extend(c.status for c in answer.checks)
    result = json.loads((source_run / "result.json").read_text())
    from .runner import summarize
    visual = aggregate(statuses)
    total = summarize(result["functional"], result["path"], visual, result["evidence"], result["environment"], result["failure_category"])
    destination = new_run(output)
    assessment = {"source_run": str(source_run.resolve()), "source_integrity_sha256": digest_file(source_run / "integrity.json"), "original_result": result["overall"], "visual": visual, "assessed_ui_result": total, "certification": "INCOMPLETE", "reviewer": review["reviewer"], "note": "External review attestation; identity is not cryptographically verified. Original evidence and result remain unchanged."}
    write_json(destination / "review.json", review)
    write_json(destination / "assessment.json", assessment)
    seal(destination)
    return destination, assessment
