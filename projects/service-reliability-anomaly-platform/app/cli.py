import argparse
from app.data_generator import generate_telemetry
from app.db import SessionLocal, init_db
from app.models import TelemetryRecord
from app.config import get_settings
from app.ml import AnomalyDetector
from app.service import ReliabilityService


def main():
    parser = argparse.ArgumentParser(description="Service reliability platform CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-data")
    gen.add_argument("--count", type=int, default=500)
    gen.add_argument("--seed", type=int, default=42)

    sub.add_parser("train")

    score = sub.add_parser("score")
    score.add_argument("--limit", type=int, default=100)

    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--count", type=int, default=1000)
    evaluate.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    init_db()
    settings = get_settings()

    if args.command == "generate-data":
        rows = generate_telemetry(args.count, args.seed)
        with SessionLocal() as session:
            session.add_all([
                TelemetryRecord(**{k: v for k, v in row.items() if k != "synthetic_anomaly"})
                for row in rows
            ])
            session.commit()
        print(f"Inserted {len(rows)} telemetry records.")
        return

    if args.command == "evaluate":
        from sklearn.metrics import precision_score, recall_score, f1_score
        rows = generate_telemetry(args.count, args.seed)
        train_rows = rows[: int(args.count * 0.7)]
        test_rows = rows[int(args.count * 0.7):]

        train_records = [TelemetryRecord(**{k: v for k, v in r.items() if k != "synthetic_anomaly"}) for r in train_rows]
        test_records = [TelemetryRecord(**{k: v for k, v in r.items() if k != "synthetic_anomaly"}) for r in test_rows]

        detector = AnomalyDetector(settings.model_path, settings.anomaly_contamination)
        detector.train(train_records)
        predictions = [x[1] for x in detector.score(test_records)]
        truth = [r["synthetic_anomaly"] for r in test_rows]

        print(f"precision={precision_score(truth, predictions, zero_division=0):.3f}")
        print(f"recall={recall_score(truth, predictions, zero_division=0):.3f}")
        print(f"f1={f1_score(truth, predictions, zero_division=0):.3f}")
        return

    with SessionLocal() as session:
        detector = AnomalyDetector(settings.model_path, settings.anomaly_contamination)
        svc = ReliabilityService(session, detector)

        if args.command == "train":
            print({"model_version": svc.train()})
        elif args.command == "score":
            decisions = svc.score_recent(args.limit)
            print(f"Scored {len(decisions)} records; anomalies={sum(d.is_anomaly for d in decisions)}")


if __name__ == "__main__":
    main()
