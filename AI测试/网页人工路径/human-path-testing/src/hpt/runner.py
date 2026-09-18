"""Only the fixed driver owns Playwright objects; routes are validated data."""
from __future__ import annotations

import time
import os
import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, expect, TimeoutError as PWTimeout

from .contracts import Route, Behavior, Environment, Step, PolicyError, origin, validate_bundle
from .evidence import Journal, write_json, new_run, digest_file, seal, utc


class Unsupported(RuntimeError):
    pass


class UIError(RuntimeError):
    pass


def runner_identity() -> dict:
    return {p.name: digest_file(p) for p in sorted(Path(__file__).parent.glob("*.py"))}


class Driver:
    def __init__(self, route: Route, behavior: Behavior, env: Environment, inputs: dict, run: Path):
        self.route, self.behavior, self.env, self.inputs, self.run = route, behavior, env, inputs, run
        self.events = Journal(run / "events.jsonl")
        self.assertions = Journal(run / "assertions.jsonl")
        self.diagnostics = Journal(run / "diagnostics.jsonl")
        self.identity = runner_identity()
        self.started = time.monotonic()
        self.observation = 0
        self.completed = []
        self.checkpoint_evidence = []
        self.popup_seen = False
        self.pw = self.browser = self.context = self.page = None

    def start(self):
        self.pw = sync_playwright().start()
        executable = os.environ.get("HPT_CHROMIUM_EXECUTABLE")
        self.browser = self.pw.chromium.launch(headless=self.env.headless, executable_path=executable or None)
        self.context = self.browser.new_context(viewport={"width": self.env.viewport_width, "height": self.env.viewport_height}, locale=self.env.locale, timezone_id=self.env.timezone)
        self.context.set_default_timeout(2500)
        self.context.tracing.start(screenshots=True, snapshots=True, sources=False)
        self.page = self.context.new_page()
        self.page.on("popup", lambda _: setattr(self, "popup_seen", True))
        self.page.on("console", lambda m: self.diagnostics.append({"type": "console", "level": m.type, "message": m.text[:1000]}) if m.type in {"error", "warning"} else None)
        self.page.on("pageerror", lambda e: self.diagnostics.append({"type": "pageerror", "message": str(e)[:1000]}))
        self.page.on("response", lambda r: self.diagnostics.append({"type": "response", "url": r.url.split("?")[0], "status": r.status}))
        self.page.on("requestfailed", lambda r: self.diagnostics.append({"type": "requestfailed", "url": r.url.split("?")[0], "failure": r.failure}))
        self.events.append({"type": "browser_started", "browser": self.browser.version, "executable": executable or "playwright-managed", "environment": self.env.model_dump(), "runner_identity": self.identity})

    def close(self):
        errors = []
        if self.context:
            try:
                self.context.tracing.stop(path=str(self.run / "trace.zip"))
            except Exception as e:
                errors.append("trace: " + str(e)[:500])
            try:
                self.context.close()
            except Exception as e:
                errors.append("context: " + str(e)[:500])
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                errors.append("browser: " + str(e)[:500])
        if self.pw:
            try:
                self.pw.stop()
            except Exception as e:
                errors.append("playwright: " + str(e)[:500])
        return errors

    def name(self, target):
        return self.inputs[target.name_param] if target.name_param is not None else target.name

    def locate(self, ref: str):
        t = self.route.targets[ref]
        root = self.locate(t.scope) if t.scope else self.page
        name = self.name(t)
        if t.by == "role":
            return root.get_by_role(t.role, name=name, exact=True)
        if t.by == "label":
            return root.get_by_label(name, exact=True)
        if t.by == "text":
            return root.get_by_text(name, exact=True)
        # The descendant cell query is evaluated in each candidate row.
        return root.get_by_role("row").filter(has=self.page.get_by_role("cell", name=name, exact=True))

    def check_deadline(self):
        if (time.monotonic() - self.started) * 1000 > self.env.run_timeout_ms:
            raise UIError("run deadline exceeded; no business action retried")
        if runner_identity() != self.identity:
            raise PolicyError("runner source changed during execution")
        if self.popup_seen:
            raise Unsupported("popup workflow requires a separately verified adapter")

    def check_origin(self):
        if self.page.url != "about:blank" and origin(self.page.url) not in self.env.allowed_origins:
            raise PolicyError("page navigated outside declared origins; navigation observed after event, not a network firewall")

    def capture(self, label: str):
        self.observation += 1
        name = f"{self.observation:04d}-{label}.png"
        path = self.run / "screenshots" / name
        self.page.screenshot(path=str(path), full_page=False, timeout=4000)
        item = {"observation_id": self.observation, "screenshot": str(path.relative_to(self.run)), "sha256": digest_file(path), "url": self.page.url, "title": self.page.title()}
        self.events.append({"type": "observation", **item})
        return item

    def guard_target(self, locator, timeout):
        expect(locator).to_have_count(1, timeout=timeout)
        expect(locator).to_be_visible(timeout=timeout)
        expect(locator).to_be_enabled(timeout=timeout)
        # Fixed, read-only inspection. No model-supplied JavaScript is accepted.
        perceptible = locator.evaluate("""e => {
          for(let n=e; n && n.nodeType===1; n=n.parentElement) {
            const s=getComputedStyle(n);
            if(s.visibility==='hidden' || s.display==='none' || Number(s.opacity)===0) return false;
          }
          return true;
        }""")
        if not perceptible:
            raise UIError("target is transparent/hidden to the user")

    def perform(self, step: Step):
        self.check_deadline()
        self.check_origin()
        before = self.capture(step.id + "-before")
        self.events.append({"type": "action_started", "step_id": step.id, "action": step.action, "target": step.target, "business_id": step.business_id, "observation_id": before["observation_id"], "monotonic_s": time.monotonic()})
        loc = self.locate(step.target) if step.target else None
        try:
            if loc is not None:
                self.guard_target(loc, step.timeout_ms)
            if step.action == "open_entry":
                self.page.goto(self.env.entry_url, wait_until="domcontentloaded", timeout=step.timeout_ms)
            elif step.action == "click":
                href = loc.get_attribute("href")
                if href:
                    dest = urljoin(self.page.url, href)
                    if origin(dest) not in self.env.allowed_origins:
                        raise PolicyError("link destination is outside declared origins or uses a disallowed scheme")
                loc.click(timeout=step.timeout_ms)
            elif step.action == "hover":
                loc.hover(timeout=step.timeout_ms)
            elif step.action in {"fill_text", "type_text"}:
                expect(loc).to_be_focused(timeout=step.timeout_ms)
                expect(loc).to_be_editable(timeout=step.timeout_ms)
                if step.action == "fill_text":
                    loc.fill(self.inputs[step.param], timeout=step.timeout_ms)
                else:
                    loc.press_sequentially(self.inputs[step.param], delay=25, timeout=step.timeout_ms)
            elif step.action == "press_key":
                self.page.keyboard.press(step.key)
            elif step.action == "select_native":
                loc.select_option(label=self.inputs[step.param], timeout=step.timeout_ms)
            elif step.action == "check":
                loc.check(timeout=step.timeout_ms)
            elif step.action == "uncheck":
                loc.uncheck(timeout=step.timeout_ms)
            elif step.action == "scroll":
                self.page.mouse.wheel(0, step.scroll_y)
            elif step.action == "reload":
                self.page.reload(wait_until="domcontentloaded", timeout=step.timeout_ms)
            elif step.action == "go_back":
                self.page.go_back(wait_until="domcontentloaded", timeout=step.timeout_ms)
            elif step.action != "checkpoint":
                raise Unsupported(step.action)
            self.check_origin()
            self.check_deadline()
            self.capture(step.id + "-after")
            self.events.append({"type": "action_finished", "step_id": step.id})
            self.completed.append(step.id)
            if step.checkpoint:
                self.verify_checkpoint(step.checkpoint, step.timeout_ms)
        except Exception as e:
            self.events.append({"type": "action_failed", "step_id": step.id, "error_type": type(e).__name__, "error": str(e)[:2000]})
            try:
                self.capture(step.id + "-failure")
            except Exception:
                pass
            raise

    def verify_checkpoint(self, ref, timeout):
        cp = self.route.checkpoints[ref]
        for i, a in enumerate(cp.assertions):
            loc = self.locate(a.target)
            value = self.inputs[a.param] if a.param is not None else a.value
            record = {"checkpoint_id": ref, "index": i, "expected": a.model_dump(), "resolved_expected": value}
            try:
                if a.kind == "visible":
                    expect(loc).to_have_count(1, timeout=timeout)
                    expect(loc).to_be_visible(timeout=timeout)
                elif a.kind == "hidden":
                    expect(loc).to_be_hidden(timeout=timeout)
                elif a.kind == "count_equals":
                    expect(loc).to_have_count(value, timeout=timeout)
                elif a.kind == "value_equals":
                    expect(loc).to_have_value(value, timeout=timeout)
                elif a.kind == "text_equals":
                    expect(loc).to_have_text(value, timeout=timeout)
                elif a.kind == "checked":
                    expect(loc).to_be_checked(timeout=timeout)
                elif a.kind == "unchecked":
                    expect(loc).not_to_be_checked(timeout=timeout)
                elif a.kind == "focused":
                    expect(loc).to_be_focused(timeout=timeout)
                elif a.kind == "disabled":
                    expect(loc).to_be_disabled(timeout=timeout)
                self.assertions.append({**record, "status": "pass", "observed": {"count": loc.count(), "texts": loc.all_text_contents()[:10]}})
            except Exception as e:
                self.assertions.append({**record, "status": "fail", "error": str(e)[:2000]})
                raise
        shot = self.capture(ref)
        self.checkpoint_evidence.append({"checkpoint_id": ref, "required_items": cp.visual, **shot})
        self.events.append({"type": "checkpoint_finished", "checkpoint_id": ref})


def summarize(functional, path, visual, evidence, environment, failure_category=None):
    if "fail" in {functional, path, visual}:
        overall = "FAIL"
    elif failure_category == "UNSUPPORTED":
        overall = "UNSUPPORTED"
    elif environment == "blocked":
        overall = "BLOCKED"
    elif functional != "pass" or path != "pass" or visual not in {"pass", "not_required"} or evidence != "complete":
        overall = "INCOMPLETE"
    else:
        overall = "PASS"
    return overall


def execute(route: Route, behavior: Behavior, env: Environment, inputs: dict, output: Path, vision=None):
    run = new_run(output)
    result = {"run_id": run.name, "case_id": route.case_id, "started_at": utc(), "functional": "not_run", "path": "unknown", "visual": "not_checked", "evidence": "incomplete", "environment": "ready", "failure_category": None, "error": None, "assurance_level": "local_runner_only", "human_equivalence": "not_certified", "stability": "first_attempt", "cleanup": "not_run", "limitations": ["No OS-level isolation: host processes and independent browser control are outside the guarantee.", "Navigation-origin checks are not a network firewall.", "Browser automation does not cover real IME or native OS dialogs."]}
    for name, obj in [("route.json", route.model_dump()), ("behavior.json", behavior.model_dump()), ("environment.json", env.model_dump()), ("inputs.json", inputs)]:
        write_json(run / name, obj)
    driver = Driver(route, behavior, env, inputs, run)
    try:
        validate_bundle(route, behavior, inputs)
        driver.start()
        for step in route.steps:
            driver.perform(step)
        result["functional"] = "pass"
        # This describes this runner's channel only, not an isolated machine.
        result["path"] = "pass"
        result["browser_version"] = driver.browser.version
    except PolicyError as e:
        result.update(path="fail", failure_category="POLICY", error=str(e))
    except Unsupported as e:
        result.update(failure_category="UNSUPPORTED", error=str(e))
    except (AssertionError, PWTimeout, UIError) as e:
        result.update(functional="fail", failure_category="UI_OR_ROUTE", error=str(e)[:3000])
    except Exception as e:
        result.update(environment="blocked" if not driver.page else "unknown", failure_category="ENVIRONMENT" if not driver.page else "RUNNER", error=str(e)[:3000])
    finally:
        try:
            errors = driver.close()
        except Exception as e:
            errors = [str(e)]
        for journal in [driver.events, driver.assertions, driver.diagnostics]:
            try:
                journal.finalize()
            except Exception as e:
                errors.append("journal finalization: " + str(e)[:500])
        write_json(run / "checkpoints.json", driver.checkpoint_evidence)
        result["completed_steps"] = driver.completed
        result["expected_steps"] = [s.id for s in route.steps]
        result["evidence_errors"] = errors
        if runner_identity() != driver.identity:
            result.update(path="fail", failure_category="POLICY", error="runner changed during run")
        result["runner_identity"] = driver.identity
    required = [x for x in driver.checkpoint_evidence if x["required_items"]]
    has_visual = any(cp.visual for cp in route.checkpoints.values())
    if not has_visual:
        result["visual"] = "not_required"
    elif vision and required:
        from .vision import check_images
        result["visual"] = check_images(run, required, vision)
    if behavior.oracle_status != "confirmed":
        result["path"] = "unknown"
        result["limitations"].append("Business oracle is pending confirmation.")
    if not errors and (run / "events.jsonl").exists() and (run / "trace.zip").exists():
        # Partial failures are valid evidence, but not complete successful coverage.
        result["evidence"] = "complete"
    # Revalidate actual referenced bytes before issuing the final conclusion.
    try:
        events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
        if [x["seq"] for x in events] != list(range(1, len(events)+1)):
            raise ValueError("event sequence gap")
        for event in events:
            if event["type"] == "observation":
                path = (run / event["screenshot"]).resolve()
                if not path.is_relative_to(run.resolve()) or not path.is_file() or digest_file(path) != event["sha256"]:
                    raise ValueError("missing or modified screenshot: " + event["screenshot"])
        if result["functional"] == "pass":
            rows = [json.loads(line) for line in (run / "assertions.jsonl").read_text().splitlines()]
            expected_assertions = {(ref, i) for ref, cp in route.checkpoints.items() for i, _ in enumerate(cp.assertions)}
            passed = {(x["checkpoint_id"], x["index"]) for x in rows if x["status"] == "pass"}
            if passed != expected_assertions or len(rows) != len(expected_assertions):
                raise ValueError("required assertion coverage is incomplete")
            if driver.completed != [s.id for s in route.steps]:
                raise ValueError("required action coverage is incomplete")
    except Exception as e:
        result["evidence"] = "incomplete"
        result["evidence_errors"].append(str(e))
    result["overall"] = summarize(result["functional"], result["path"], result["visual"], result["evidence"], result["environment"], result["failure_category"])
    result["certification"] = "INCOMPLETE" if result["overall"] == "PASS" else result["overall"]
    result["finished_at"] = utc()
    write_json(run / "result.json", result)
    from .reporting import render_report
    render_report(run, result)
    seal(run)
    return run, result
