"""Pure dependency-graph operations, independent of SQL parsing."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from typing import Any

from .errors import DuplicateModelError, UnknownModelError


@dataclass(frozen=True, slots=True)
class ParsedModel:
    name: str
    file: str
    references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelLineage:
    name: str
    file: str
    dependencies: tuple[str, ...]
    external_dependencies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LineageReport:
    schema_version: int
    dialect: str
    models: tuple[ModelLineage, ...]
    edges: tuple[dict[str, str], ...]
    cycles: tuple[tuple[str, ...], ...]
    topological_order: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a stable JSON-compatible mapping."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ImpactItem:
    model: str
    file: str
    distance: int


@dataclass(frozen=True, slots=True)
class ImpactReport:
    schema_version: int
    changed: tuple[str, ...]
    affected: tuple[ImpactItem, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _canonical_cycle(nodes: list[str]) -> tuple[str, ...]:
    """Rotate a cycle so the lexicographically smallest node is first."""
    if not nodes:
        return ()
    pivot = min(range(len(nodes)), key=nodes.__getitem__)
    rotated = nodes[pivot:] + nodes[:pivot]
    return tuple(rotated + [rotated[0]])


def _find_cycles(dependencies: dict[str, set[str]]) -> tuple[tuple[str, ...], ...]:
    state = {name: 0 for name in dependencies}
    stack: list[str] = []
    found: set[tuple[str, ...]] = set()

    def visit(name: str) -> None:
        state[name] = 1
        stack.append(name)
        for dependency in sorted(dependencies[name]):
            if state[dependency] == 0:
                visit(dependency)
            elif state[dependency] == 1:
                start = stack.index(dependency)
                found.add(_canonical_cycle(stack[start:]))
        stack.pop()
        state[name] = 2

    for name in sorted(dependencies):
        if state[name] == 0:
            visit(name)
    return tuple(sorted(found))


def build_report(parsed_models: list[ParsedModel], dialect: str) -> LineageReport:
    """Resolve parsed table references into a deterministic model dependency graph."""
    names: dict[str, ParsedModel] = {}
    for model in parsed_models:
        key = model.name.casefold()
        if key in names:
            previous = names[key]
            raise DuplicateModelError(
                f"Duplicate model name '{model.name}' in '{previous.file}' and '{model.file}'"
            )
        names[key] = model

    dependencies: dict[str, set[str]] = {name: set() for name in names}
    external: dict[str, set[str]] = {name: set() for name in names}

    for name, model in names.items():
        for reference in model.references:
            leaf = reference.rsplit(".", maxsplit=1)[-1].casefold()
            if leaf in names:
                dependencies[name].add(leaf)
            else:
                external[name].add(reference)

    reverse: dict[str, set[str]] = {name: set() for name in names}
    for downstream, upstream_models in dependencies.items():
        for upstream in upstream_models:
            reverse[upstream].add(downstream)

    indegree = {name: len(dependencies[name]) for name in names}
    ready = deque(sorted(name for name, degree in indegree.items() if degree == 0))
    topo: list[str] = []
    while ready:
        upstream = ready.popleft()
        topo.append(upstream)
        for downstream in sorted(reverse[upstream]):
            indegree[downstream] -= 1
            if indegree[downstream] == 0:
                ready.append(downstream)
        # Keep the queue deterministic when multiple newly-ready nodes appear.
        ready = deque(sorted(ready))

    model_records = tuple(
        ModelLineage(
            name=name,
            file=names[name].file,
            dependencies=tuple(sorted(dependencies[name])),
            external_dependencies=tuple(sorted(external[name])),
        )
        for name in sorted(names)
    )
    edges = tuple(
        {"upstream": upstream, "downstream": downstream}
        for upstream in sorted(reverse)
        for downstream in sorted(reverse[upstream])
    )
    return LineageReport(
        schema_version=1,
        dialect=dialect,
        models=model_records,
        edges=edges,
        cycles=_find_cycles(dependencies),
        topological_order=tuple(topo),
    )


def build_impact(report: LineageReport, changed_names: list[str]) -> ImpactReport:
    """Return the transitive downstream impact with shortest graph distances."""
    by_name = {model.name: model for model in report.models}
    changed = tuple(sorted({name.casefold() for name in changed_names}))
    if not changed:
        raise UnknownModelError("At least one --changed model is required")
    unknown = sorted(set(changed) - set(by_name))
    if unknown:
        raise UnknownModelError("Unknown changed model(s): " + ", ".join(unknown))

    dependents: dict[str, set[str]] = {name: set() for name in by_name}
    for model in report.models:
        for dependency in model.dependencies:
            dependents[dependency].add(model.name)

    distances: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque((name, 0) for name in changed)
    visited = set(changed)
    while queue:
        current, distance = queue.popleft()
        for downstream in sorted(dependents[current]):
            if downstream in visited:
                continue
            visited.add(downstream)
            distances[downstream] = distance + 1
            queue.append((downstream, distance + 1))

    items = tuple(
        ImpactItem(model=name, file=by_name[name].file, distance=distance)
        for name, distance in sorted(distances.items(), key=lambda item: (item[1], item[0]))
    )
    return ImpactReport(schema_version=1, changed=changed, affected=items)
