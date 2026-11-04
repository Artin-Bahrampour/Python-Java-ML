import argparse,joblib
from pathlib import Path
from app.core import synthetic,train
def main():
 p=argparse.ArgumentParser();p.add_argument("--synthetic",action="store_true");p.add_argument("--output",default="artifacts/demand.joblib");a=p.parse_args()
 if not a.synthetic:p.error("demo requires --synthetic")
 b,_=train(synthetic());o=Path(a.output);o.parent.mkdir(parents=True,exist_ok=True);joblib.dump(b,o);print(b["metrics"])
if __name__=="__main__":main()
