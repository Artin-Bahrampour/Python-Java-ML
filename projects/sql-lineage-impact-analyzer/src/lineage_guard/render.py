"""Stable JSON and text rendering for analysis and impact reports."""

from __future__ import annotations

import json

from .graph import ImpactReport, LineageReport


def render_lineage_json(report: LineageReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_lineage_text(report: LineageReport) -> str:
    lines = [
        "SQL Lineage Report",
        f"Dialect: {report.dialect}",
        f"Models: {len(report.models)}",
        f"Dependency edges: {len(report.edges)}",
        f"Cycles: {len(report.cycles)}",
        "",
    ]
    if report.cycles:
        lines.append("Detected cycles:")
        lines.extend("  " + " -> ".join(cycle) for cycle in report.cycles)
        lines.append("")
    lines.append("Build order:")
    if report.topological_order:
        lines.extend(
            f"  {index}. {name}" for index, name in enumerate(report.topological_order, start=1)
        )
    else:
        lines.append("  unavailable (dependency cycle)")
    lines.extend(["", "Models:"])
    for model in report.models:
        lines.append(f"  {model.name} ({model.file})")
        lines.append(
            "    depends on: " + (", ".join(model.dependencies) if model.dependencies else "none")
        )
        lines.append(
            "    external: "
            + (", ".join(model.external_dependencies) if model.external_dependencies else "none")
        )
    return "\n".join(lines) + "\n"


def render_impact_json(report: ImpactReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_impact_text(report: ImpactReport) -> str:
    lines = [
        "SQL Change Impact Report",
        "Changed models: " + ", ".join(report.changed),
        f"Affected downstream models: {len(report.affected)}",
    ]
    if not report.affected:
        lines.append("No downstream models are affected.")
    else:
        lines.append("")
        lines.append("Impact (nearest first):")
        lines.extend(
            f"  distance={item.distance}  {item.model} ({item.file})" for item in report.affected
        )
    return "\n".join(lines) + "\n"
