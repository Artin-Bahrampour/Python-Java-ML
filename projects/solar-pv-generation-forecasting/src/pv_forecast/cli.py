"""Command-line interface for generation, training, scoring, and drift checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pv_forecast.data import generate_dataset, load_dataset
from pv_forecast.modeling import load_bundle, predict_frame, train_and_evaluate
from pv_forecast.monitoring import feature_drift_report


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pv-forecast",
        description="Leakage-aware solar PV generation forecasting",
    )
    commands = parser.add_subparsers(dest="command")

    generate = commands.add_parser("generate", help="Generate deterministic synthetic hourly data")
    generate.add_argument("--output", default="data/generated/pv_hourly.csv")
    generate.add_argument("--days", type=int, default=730)
    generate.add_argument("--seed", type=int, default=42)

    train = commands.add_parser("train", help="Train and evaluate candidate forecasting models")
    train.add_argument("--data", required=True)
    train.add_argument("--artifacts-dir", default="artifacts")
    train.add_argument("--seed", type=int, default=42)

    evaluate = commands.add_parser("evaluate", help="Print saved evaluation metrics")
    evaluate.add_argument("--artifacts-dir", default="artifacts")

    predict = commands.add_parser("predict", help="Score a CSV dataset")
    predict.add_argument("--data", required=True)
    predict.add_argument("--artifacts-dir", default="artifacts")
    predict.add_argument("--output", default="artifacts/predictions.csv")

    monitor = commands.add_parser("monitor", help="Compare feature distributions using PSI")
    monitor.add_argument("--reference", required=True)
    monitor.add_argument("--current", required=True)
    monitor.add_argument("--output", default="artifacts/drift-report.json")
    monitor.add_argument("--threshold", type=float, default=0.2)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "generate":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        frame = generate_dataset(days=args.days, seed=args.seed)
        frame.to_csv(output, index=False)
        print(f"Wrote {len(frame):,} validated rows to {output}")
    elif args.command == "train":
        frame = load_dataset(args.data, require_target=True)
        report = train_and_evaluate(frame, args.artifacts_dir, seed=args.seed)
        print(json.dumps(report, indent=2))
    elif args.command == "evaluate":
        metrics_path = Path(args.artifacts_dir) / "metrics.json"
        if not metrics_path.exists():
            raise SystemExit("metrics.json not found; run train first")
        print(metrics_path.read_text(encoding="utf-8"))
    elif args.command == "predict":
        frame = load_dataset(args.data, require_target=False)
        bundle = load_bundle(Path(args.artifacts_dir) / "model_bundle.joblib")
        predictions = predict_frame(frame, bundle)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(output, index=False)
        print(f"Wrote {len(predictions):,} predictions to {output}")
    elif args.command == "monitor":
        reference = load_dataset(args.reference, require_target=False)
        current = load_dataset(args.current, require_target=False)
        report = feature_drift_report(reference, current, threshold=args.threshold)
        _write_json(Path(args.output), report)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
