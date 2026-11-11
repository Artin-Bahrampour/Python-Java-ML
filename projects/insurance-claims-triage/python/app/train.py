import argparse, joblib
from pathlib import Path
from .core import sample, fit

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--output",default="artifacts/claims.joblib"); args=p.parse_args()
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(fit(*sample()),args.output); print(f"saved {args.output}")
