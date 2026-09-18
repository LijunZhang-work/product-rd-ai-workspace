"""Ten explicit fixture cases. These are authored test cases, not claimed AI exploration."""
from __future__ import annotations
from pathlib import Path
from uuid import uuid4
from .contracts import Route, Behavior, Environment
from .evidence import write_json

CASE_NAMES = ["create", "required", "duplicate", "cancel", "search", "pagination", "edit", "keyboard", "delete", "empty_search"]


def make_case(name="create", base_url="http://127.0.0.1:8765", visual=True, device_name=None):
    if name not in CASE_NAMES:
        raise ValueError("unknown example case")
    inputs = {"device_name": device_name or "Test-" + uuid4().hex[:8], "device_type": "PCS"}
    targets = {
        "nav": {"by": "role", "role": "link", "name": "Devices"},
        "heading": {"by": "role", "role": "heading", "name": "Device management"},
        "add": {"by": "role", "role": "button", "name": "Add device"},
        "dialog": {"by": "role", "role": "dialog", "name": "Add device"},
        "name": {"by": "label", "name": "Device name", "scope": "dialog"},
        "type": {"by": "role", "role": "combobox", "name": "Device type", "scope": "dialog"},
        "option": {"by": "role", "role": "option", "name_param": "device_type"},
        "save": {"by": "role", "role": "button", "name": "Save", "scope": "dialog"},
        "cancel": {"by": "role", "role": "button", "name": "Cancel", "scope": "dialog"},
        "status": {"by": "role", "role": "status", "name": "Device saved"},
        "row": {"by": "row_with_cell", "name_param": "device_name"},
        "type_cell": {"by": "role", "role": "cell", "name_param": "device_type", "scope": "row"},
        "alert": {"by": "role", "role": "alert", "scope": "dialog", "name": ""},
        "search": {"by": "role", "role": "textbox", "name": "Search devices"},
        "search_button": {"by": "role", "role": "button", "name": "Search"},
        "next": {"by": "role", "role": "button", "name": "Next"},
        "prev": {"by": "role", "role": "button", "name": "Previous"},
        "edit": {"by": "role", "role": "button", "name": "Edit", "scope": "original"},
        "original": {"by": "row_with_cell", "name": "Original"},
        "delete": {"by": "role", "role": "button", "name": "Delete", "scope": "row"},
        "delete_dialog": {"by": "role", "role": "dialog", "name": "Delete device"},
        "confirm": {"by": "role", "role": "button", "name": "Confirm delete", "scope": "delete_dialog"},
        "deleted": {"by": "role", "role": "status", "name": "Device deleted"},
        "empty": {"by": "text", "name": "No devices found"},
        "table_rows": {"by": "role", "role": "row", "name": "", "exact": True},
        "first": {"by": "row_with_cell", "name": "Page-1"}
    }
    # Unused targets are retained in the frozen contract for readable templates.
    steps, cps = [], {}

    def add(action, target=None, param=None, checkpoint=None, assertions=None, visual_text=None, **kw):
        ident = f"S{len(steps)+1:02d}"
        s = {"id": ident, "business_id": ident, "action": action, **kw}
        if target is not None:
            s["target"] = target
        if param is not None:
            s["param"] = param
        if checkpoint:
            s["checkpoint"] = checkpoint
            cps[checkpoint] = {"assertions": assertions, "visual": [visual_text] if visual and visual_text else []}
        steps.append(s)

    add("open_entry")
    pre = [{"target": "heading", "kind": "visible"}]
    if name in {"create", "keyboard", "cancel", "edit"}:
        pre.append({"target": "row", "kind": "count_equals", "value": 0})
    add("click", "nav", checkpoint="CP_LIST", assertions=pre)
    if name in {"search", "empty_search"}:
        add("click", "search")
        add("fill_text", "search", "device_name")
        if name == "search":
            final = [{"target": "row", "kind": "count_equals", "value": 1}, {"target": "row", "kind": "visible"}]
        else:
            final = [{"target": "row", "kind": "count_equals", "value": 0}, {"target": "empty", "kind": "visible"}]
        add("click", "search_button", checkpoint="CP_SEARCH", assertions=final, visual_text="The search result area is visible, legible, and not obscured by another panel.")
    elif name == "pagination":
        inputs["device_name"] = "Page-6"
        add("click", "next", checkpoint="CP_NEXT", assertions=[{"target": "row", "kind": "visible"}], visual_text="Page 2 and device Page-6 are visibly displayed.")
        add("click", "prev", checkpoint="CP_PREVIOUS", assertions=[{"target": "first", "kind": "visible"}])
    elif name == "delete":
        add("click", "delete", checkpoint="CP_CONFIRM", assertions=[{"target": "delete_dialog", "kind": "visible"}], visual_text="The delete confirmation dialog is visible and its controls are readable.")
        add("click", "confirm", checkpoint="CP_DELETED", assertions=[{"target": "row", "kind": "count_equals", "value": 0}, {"target": "deleted", "kind": "visible"}], visual_text="A readable Device deleted success message is visible.")
        add("reload", checkpoint="CP_RELOADED", assertions=[{"target": "row", "kind": "count_equals", "value": 0}, {"target": "heading", "kind": "visible"}])
    else:
        if name == "edit":
            targets["dialog"]["name"] = "Edit device"
        add("click", "edit" if name == "edit" else "add", checkpoint="CP_DIALOG", assertions=[{"target": "dialog", "kind": "visible"}], visual_text="The device form is visible, with readable Device name and Device type labels.")
        add("click", "name")
        if name == "required":
            inputs["device_name"] = ""
        add("type_text" if name == "keyboard" else "fill_text", "name", "device_name")
        add("click", "type")
        add("click", "option", checkpoint="CP_FORM", assertions=[{"target": "name", "kind": "value_equals", "param": "device_name"}, {"target": "type", "kind": "text_equals", "param": "device_type"}], visual_text="The device name input and selected equipment type are readable; the Save control is visible.")
        if name == "cancel":
            add("click", "cancel", checkpoint="CP_CANCELLED", assertions=[{"target": "dialog", "kind": "hidden"}, {"target": "row", "kind": "count_equals", "value": 0}])
            add("reload", checkpoint="CP_RELOADED", assertions=[{"target": "row", "kind": "count_equals", "value": 0}, {"target": "heading", "kind": "visible"}])
        elif name in {"required", "duplicate"}:
            text = "Device name is required" if name == "required" else "Name already exists"
            add("click", "save", checkpoint="CP_VALIDATION", assertions=[{"target": "alert", "kind": "text_equals", "value": text}, {"target": "dialog", "kind": "visible"}], visual_text=f"The validation message {text!r} is readable in the form.")
        else:
            add("click", "save", checkpoint="CP_SAVED", assertions=[{"target": "status", "kind": "visible"}, {"target": "dialog", "kind": "hidden"}], visual_text="Device saved is visibly displayed in the success message.")
            add("reload", checkpoint="CP_PERSISTED", assertions=[{"target": "row", "kind": "count_equals", "value": 1}, {"target": "row", "kind": "visible"}, {"target": "type_cell", "kind": "visible"}], visual_text="The device list is legible and the created or edited device row is visibly displayed with its equipment type.")
    route = Route.model_validate({"case_id": "device." + name, "revision": 1, "summary": "Fixture UI scenario: " + name, "parameters": {"device_name": {"min_length": 0 if name == "required" else 1, "max_length": 32}, "device_type": {"choices": ["PCS", "Inverter"]}}, "targets": targets, "steps": steps, "checkpoints": cps})
    behavior = Behavior(case_id=route.case_id, revision=1, original_intent=route.summary, oracle_status="confirmed", required_steps=route.steps, required_targets=route.targets, required_checkpoints=route.checkpoints, excluded=["Real product integration", "Native dialogs and IME", "Other browsers"] + ([] if visual else ["All visual semantic checks: this is a functional-only test profile."]))
    env = Environment(name="fixture", entry_url=base_url + "/", allowed_origins=[base_url], app_build="fixture-v1")
    return route, behavior, env, inputs


def seed_case(fixture, name, inputs):
    if name in {"duplicate", "search", "delete"}:
        fixture.seed(inputs["device_name"])
    if name == "edit":
        fixture.seed("Original")
    if name in {"search", "empty_search"}:
        fixture.seed("Unrelated")
    if name == "pagination":
        for i in range(1, 7):
            fixture.seed(f"Page-{i}")


def save_example(destination: Path, name="create", base_url="http://127.0.0.1:8765", visual=True):
    destination.mkdir(parents=True, exist_ok=False)
    route, behavior, env, inputs = make_case(name, base_url, visual)
    for filename, obj in [("route.json", route.model_dump()), ("behavior.json", behavior.model_dump()), ("environment.json", env.model_dump()), ("inputs.json", inputs)]:
        write_json(destination / filename, obj)
    return destination

