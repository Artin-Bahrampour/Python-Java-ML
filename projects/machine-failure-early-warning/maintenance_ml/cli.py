"""Command-line entry point."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .pipeline import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a machine failure early-warning model")
    parser.add_argument("--output", type=Path, default=Path("reports"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    metrics, predictions = evaluate(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with (args.output / "predictions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)
    print(json.dumps({"metrics_file": str(args.output / "metrics.json"),
                      "selected_threshold": metrics["selected_threshold"],
                      "logistic_regression": metrics["logistic_regression"],
                      "vibration_rule_baseline": metrics["vibration_rule_baseline"]}, indent=2))


if __name__ == "__main__":
    main()
