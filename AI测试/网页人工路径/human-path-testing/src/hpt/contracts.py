"""Strict data contracts. No user expressions, code, imports or arbitrary methods."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PolicyError(ValueError):
    pass


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Parameter(Strict):
    min_length: int = Field(default=1, ge=0, le=4096)
    max_length: int = Field(default=128, ge=1, le=4096)
    choices: list[str] = Field(default_factory=list, max_length=100)


class Target(Strict):
    by: Literal["role", "label", "text", "row_with_cell"]
    role: str | None = None
    name: str | None = None
    name_param: str | None = None
    scope: str | None = None
    exact: Literal[True] = True

    @model_validator(mode="after")
    def shape(self):
        if (self.name is None) == (self.name_param is None):
            raise ValueError("target requires exactly one of name/name_param")
        if (self.by == "role") != (self.role is not None):
            raise ValueError("role is required only for role target")
        return self


class Assertion(Strict):
    target: str
    kind: Literal["visible", "hidden", "value_equals", "text_equals", "count_equals", "checked", "unchecked", "focused", "disabled"]
    value: str | int | None = None
    param: str | None = None

    @model_validator(mode="after")
    def shape(self):
        if self.kind in {"value_equals", "text_equals"}:
            if (self.value is None) == (self.param is None):
                raise ValueError("comparison requires exactly one value/param")
            if self.value is not None and type(self.value) is not str:
                raise ValueError("text comparison requires string")
        elif self.kind == "count_equals":
            if type(self.value) is not int or self.value < 0 or self.param is not None:
                raise ValueError("count requires nonnegative integer")
        elif self.value is not None or self.param is not None:
            raise ValueError("unexpected assertion value")
        return self


class Checkpoint(Strict):
    assertions: list[Assertion] = Field(min_length=1, max_length=50)
    visual: list[str] = Field(default_factory=list, max_length=20)


Action = Literal["open_entry", "click", "hover", "fill_text", "type_text", "press_key", "select_native", "check", "uncheck", "scroll", "reload", "go_back", "checkpoint"]


class Step(Strict):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    business_id: str
    action: Action
    target: str | None = None
    param: str | None = None
    key: Literal["Tab", "Shift+Tab", "Enter", "Escape", "ArrowDown", "ArrowUp", "Space", "Backspace", "ControlOrMeta+A"] | None = None
    scroll_y: int | None = Field(default=None, ge=-2000, le=2000)
    checkpoint: str | None = None
    timeout_ms: int = Field(default=2500, ge=100, le=15000)

    @model_validator(mode="after")
    def shape(self):
        target_actions = {"click", "hover", "fill_text", "type_text", "select_native", "check", "uncheck"}
        if (self.action in target_actions) != (self.target is not None):
            raise ValueError("target field does not match action")
        if (self.action in {"fill_text", "type_text", "select_native"}) != (self.param is not None):
            raise ValueError("param field does not match action")
        if (self.action == "press_key") != (self.key is not None):
            raise ValueError("key field does not match action")
        if (self.action == "scroll") != (self.scroll_y is not None):
            raise ValueError("scroll_y field does not match action")
        if self.action == "checkpoint" and not self.checkpoint:
            raise ValueError("checkpoint action needs checkpoint reference")
        return self


class Route(Strict):
    schema_version: Literal["1.1"] = "1.1"
    case_id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,80}$")
    revision: int = Field(ge=1)
    summary: str = Field(min_length=1, max_length=3000)
    parameters: dict[str, Parameter]
    targets: dict[str, Target]
    checkpoints: dict[str, Checkpoint]
    steps: list[Step] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def references(self):
        if self.case_id in {".", ".."}:
            raise ValueError("invalid case id")
        for mapping in [self.targets, self.parameters, self.checkpoints]:
            if len(mapping) > 200 or any(not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", k) for k in mapping):
                raise ValueError("invalid identifier or too many definitions")
        if len({s.id for s in self.steps}) != len(self.steps):
            raise ValueError("duplicate step id")
        if self.steps[0].action != "open_entry" or sum(s.action == "open_entry" for s in self.steps) != 1:
            raise ValueError("one open_entry is required as the first step")
        reached = []
        for s in self.steps:
            if s.target is not None and s.target not in self.targets:
                raise ValueError(f"missing target: {s.target}")
            if s.param is not None and s.param not in self.parameters:
                raise ValueError(f"missing parameter: {s.param}")
            if s.checkpoint is not None:
                if s.checkpoint not in self.checkpoints:
                    raise ValueError("missing checkpoint")
                reached.append(s.checkpoint)
        if len(reached) != len(set(reached)) or set(reached) != set(self.checkpoints):
            raise ValueError("each checkpoint must be reached exactly once")
        for name, t in self.targets.items():
            if t.name_param is not None and t.name_param not in self.parameters:
                raise ValueError("missing target parameter")
            seen = {name}
            while t.scope is not None:
                if t.scope in seen or t.scope not in self.targets:
                    raise ValueError("target scope missing or cyclic")
                seen.add(t.scope)
                t = self.targets[t.scope]
        for cp in self.checkpoints.values():
            for a in cp.assertions:
                if a.target not in self.targets or (a.param is not None and a.param not in self.parameters):
                    raise ValueError("assertion reference missing")
        return self


class Behavior(Strict):
    case_id: str
    revision: int = Field(ge=1)
    original_intent: str = Field(min_length=1)
    oracle_status: Literal["confirmed", "pending"]
    # This separate file freezes the intent's required action/check coverage.
    required_steps: list[Step] = Field(min_length=1, max_length=100)
    required_targets: dict[str, Target]
    required_checkpoints: dict[str, Checkpoint]
    excluded: list[str] = Field(default_factory=list)


class Environment(Strict):
    name: str
    entry_url: str
    allowed_origins: list[str] = Field(min_length=1, max_length=30)
    app_build: str = "unknown"
    role: str = "test-user"
    viewport_width: int = Field(default=1280, ge=320, le=3840)
    viewport_height: int = Field(default=900, ge=400, le=2160)
    locale: str = "en-US"
    timezone: str = "UTC"
    headless: bool = True
    run_timeout_ms: int = Field(default=120000, ge=1000, le=600000)

    @model_validator(mode="after")
    def urls(self):
        for value in [self.entry_url, *self.allowed_origins]:
            u = urlsplit(value)
            if u.scheme not in {"http", "https"} or not u.hostname or u.username or u.password:
                raise ValueError("only normal HTTP(S) URLs without embedded credentials are supported")
        if origin(self.entry_url) not in self.allowed_origins:
            raise ValueError("entry origin is not allowed")
        if any(origin(x) != x for x in self.allowed_origins):
            raise ValueError("allowed_origins must contain exact origins without paths")
        return self


def origin(url: str) -> str:
    u = urlsplit(url)
    port = u.port
    default = (u.scheme == "http" and port == 80) or (u.scheme == "https" and port == 443)
    host = u.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    return f"{u.scheme}://{host}" + (f":{port}" if port and not default else "")


def read_json(path: str | Path):
    p = Path(path)
    if p.stat().st_size > 2_000_000:
        raise PolicyError("configuration exceeds 2 MB limit")
    return json.loads(p.read_text(encoding="utf-8"))


def validate_bundle(route: Route, behavior: Behavior, inputs: dict) -> None:
    if route.case_id != behavior.case_id:
        raise PolicyError("case does not match independent behavior contract")
    if route.steps != behavior.required_steps or route.targets != behavior.required_targets or route.checkpoints != behavior.required_checkpoints:
        raise PolicyError("route changes frozen business actions, target semantics or expected results")
    if set(inputs) != set(route.parameters):
        raise PolicyError("input parameter set does not match route")
    for k, p in route.parameters.items():
        value = inputs[k]
        if type(value) is not str or not p.min_length <= len(value) <= p.max_length:
            raise PolicyError(f"invalid string parameter: {k}")
        if p.choices and value not in p.choices:
            raise PolicyError(f"parameter outside declared choices: {k}")
