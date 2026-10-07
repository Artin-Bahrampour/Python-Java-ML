"""Typed report models for deterministic compatibility results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

Severity = Literal["breaking", "warning", "info"]


@dataclass(frozen=True, slots=True)
class Finding:
    rule_id: str
    severity: Severity
    location: str
    message: str
    before: Any = None
    after: Any = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        return {key: value for key, value in result.items() if value is not None}


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    baseline: str
    candidate: str
    findings: tuple[Finding, ...]

    @property
    def breaking_count(self) -> int:
        return sum(finding.severity == "breaking" for finding in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(finding.severity == "warning" for finding in self.findings)

    @property
    def compatible(self) -> bool:
        return self.breaking_count == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": "openapi-compatibility-gate",
            "report_version": 1,
            "baseline": self.baseline,
            "candidate": self.candidate,
            "summary": {
                "compatible": self.compatible,
                "breaking": self.breaking_count,
                "warnings": self.warning_count,
                "total_findings": len(self.findings),
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }
