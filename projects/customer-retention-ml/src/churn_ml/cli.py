from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from churn_ml.data import generate_customers, load_csv
from churn_ml.modeling import load_bundle, train_and_evaluate


def main() -> None:
    parser = argparse.ArgumentParser(prog="churn-ml", description="Customer churn risk modeling")
    subs = parser.add_subparsers(dest="command")
    gen = subs.add_parser("generate")
    gen.add_argument("--output", default="data/generated/customers.csv")
    gen.add_argument("--rows", type=int, default=5000)
    gen.add_argument("--seed", type=int, default=42)
    train = subs.add_parser("train")
    train.add_argument("--data", required=True)
    train.add_argument("--artifacts-dir", default="artifacts")
    train.add_argument("--seed", type=int, default=42)
    ev = subs.add_parser("evaluate")
    ev.add_argument("--artifacts-dir", default="artifacts")
    pred = subs.add_parser("predict")
    pred.add_argument("--data", required=True)
    pred.add_argument("--artifacts-dir", default="artifacts")
    pred.add_argument("--output", default="artifacts/scores.csv")
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == "generate":
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        df = generate_customers(args.rows, args.seed)
        df.to_csv(path, index=False)
        print(f"Wrote {len(df):,} records to {path}")
    elif args.command == "train":
        print(
            json.dumps(
                train_and_evaluate(load_csv(args.data), args.artifacts_dir, args.seed), indent=2
            )
        )
    elif args.command == "evaluate":
        path = Path(args.artifacts_dir) / "metrics.json"
        if not path.exists():
            raise SystemExit("metrics.json not found; run train first")
        print(path.read_text(encoding="utf-8"))
    elif args.command == "predict":
        df = load_csv(args.data, False)
        bundle = load_bundle(Path(args.artifacts_dir) / "model_bundle.joblib")
        model = bundle["models"][bundle["selected_model"]]
        output = df[bundle["feature_columns"]].copy()
        output["churn_risk"] = model.predict_proba(output)[:, 1].round(6)
        output["risk_band"] = pd.cut(
            output["churn_risk"],
            [-0.001, 0.30, 0.60, 1.0],
            labels=["low", "medium", "high"],
            include_lowest=True,
        ).astype(str)
        dest = Path(args.output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        output.to_csv(dest, index=False)
        print(f"Wrote {len(output):,} risk scores to {dest}")


if __name__ == "__main__":
    main()
