from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv, json, math, re
from pathlib import Path
from typing import Any

@dataclass
class CheckResult:
    check: str
    passed: bool
    message: str
    severity: str = "error"
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationReport:
    dataset: str
    contract: str
    started_at: str
    finished_at: str
    rows: int
    passed: bool
    checks: list[CheckResult]
    profile: dict[str, Any]

    def to_dict(self):
        return {"dataset": self.dataset, "contract": self.contract, "started_at": self.started_at,
                "finished_at": self.finished_at, "rows": self.rows, "passed": self.passed,
                "checks": [c.__dict__ for c in self.checks], "profile": self.profile}

class ContractError(ValueError): pass

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def load_contract(path: Path) -> dict[str, Any]:
    import yaml
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or "columns" not in data:
        raise ContractError("Contract must contain a 'columns' mapping")
    return data

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ContractError("Dataset has no header")
        return list(reader)

def profile(rows: list[dict[str, str]], columns: dict[str, Any]) -> dict[str, Any]:
    result = {"row_count": len(rows), "columns": {}}
    for name, spec in columns.items():
        vals = [r.get(name, "") for r in rows]
        nonempty = [v for v in vals if v not in (None, "")]
        entry: dict[str, Any] = {"null_count": len(vals)-len(nonempty), "distinct_count": len(set(nonempty))}
        typ = spec.get("type", "string")
        if typ in {"integer", "number"}:
            nums=[]
            for v in nonempty:
                try: nums.append(float(v))
                except ValueError: pass
            if nums:
                entry.update(min=min(nums), max=max(nums), mean=sum(nums)/len(nums))
        result["columns"][name]=entry
    return result

def validate(rows: list[dict[str, str]], contract: dict[str, Any], dataset: str, contract_name: str) -> ValidationReport:
    started=datetime.now(timezone.utc).isoformat()
    checks=[]
    columns=contract["columns"]
    expected=set(columns); actual=set(rows[0].keys()) if rows else set(columns)
    missing=sorted(expected-actual); extra=sorted(actual-expected)
    checks.append(CheckResult("schema", not missing, "Schema matches contract" if not missing else f"Missing columns: {missing}", details={"missing":missing,"extra":extra}))
    if extra and contract.get("reject_unknown_columns", False):
        checks[-1]=CheckResult("schema", False, f"Unknown columns: {extra}", details={"missing":missing,"extra":extra})
    for name,spec in columns.items():
        vals=[r.get(name, "") for r in rows]
        nulls=sum(v in (None, "") for v in vals)
        max_null=spec.get("max_null_ratio")
        if max_null is not None:
            ratio=nulls/max(1,len(vals)); checks.append(CheckResult(f"null_ratio:{name}", ratio<=max_null, f"Null ratio {ratio:.3f} <= {max_null:.3f}", details={"ratio":ratio}))
        if spec.get("unique"):
            nonempty=[v for v in vals if v not in (None, "")]
            ok=len(nonempty)==len(set(nonempty)); checks.append(CheckResult(f"unique:{name}", ok, "Values are unique" if ok else "Duplicate values detected"))
        typ=spec.get("type","string")
        bad=[]
        for i,v in enumerate(vals,1):
            if v in (None, "") and spec.get("nullable", True): continue
            try:
                if typ=="integer": int(v)
                elif typ=="number": x=float(v); assert math.isfinite(x)
                elif typ=="boolean" and str(v).lower() not in {"true","false","1","0"}: raise ValueError
                elif typ=="email" and not EMAIL_RE.match(str(v)): raise ValueError
            except (ValueError, AssertionError, TypeError): bad.append(i)
        if bad: checks.append(CheckResult(f"type:{name}",False,f"Invalid {typ} values at {len(bad)} row(s)",details={"rows":bad[:20]}))
        else: checks.append(CheckResult(f"type:{name}",True,f"Column conforms to {typ}"))
        if "allowed" in spec:
            allowed=set(map(str,spec["allowed"])); bad=[i for i,v in enumerate(vals,1) if v not in allowed and not (v=="" and spec.get("nullable",True))]
            checks.append(CheckResult(f"allowed:{name}", not bad, "Allowed-value constraint satisfied" if not bad else f"Disallowed values at {len(bad)} row(s)", details={"rows":bad[:20]}))
    finished=datetime.now(timezone.utc).isoformat()
    return ValidationReport(dataset,contract_name,started,finished,len(rows),all(c.passed or c.severity!="error" for c in checks),checks,profile(rows,columns))

def write_report(report: ValidationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(report.to_dict(),indent=2),encoding="utf-8")
    tmp.replace(path)
