from __future__ import annotations
import argparse, json, logging, sys
from pathlib import Path
from .core import load_contract, read_csv, validate, write_report

def main() -> int:
    ap=argparse.ArgumentParser(description="Validate batch datasets against explicit data contracts")
    ap.add_argument("dataset", type=Path); ap.add_argument("--contract", required=True, type=Path)
    ap.add_argument("--report", type=Path, default=Path("build/report.json"))
    args=ap.parse_args(); logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    try:
        contract=load_contract(args.contract); rows=read_csv(args.dataset)
        report=validate(rows,contract,args.dataset.name,args.contract.name); write_report(report,args.report)
        print(json.dumps({"passed":report.passed,"rows":report.rows,"failed_checks":sum(not c.passed for c in report.checks)},indent=2))
        return 0 if report.passed else 2
    except Exception as exc:
        logging.error("validation_failed error=%s",exc); return 1
if __name__=="__main__": raise SystemExit(main())
