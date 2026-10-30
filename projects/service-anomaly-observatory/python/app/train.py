import argparse,joblib,pandas as pd
from pathlib import Path
from app.core import synthetic,train
def main():
 p=argparse.ArgumentParser();p.add_argument("--synthetic",action="store_true");p.add_argument("--input");p.add_argument("--output",default="artifacts/anomaly.joblib");a=p.parse_args()
 if bool(a.input)==a.synthetic:p.error("choose exactly one source")
 b,m=train(synthetic() if a.synthetic else pd.read_csv(a.input));o=Path(a.output);o.parent.mkdir(parents=True,exist_ok=True);joblib.dump(b,o);print(m)
if __name__=="__main__":main()
