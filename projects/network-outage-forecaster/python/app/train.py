import argparse,joblib
from pathlib import Path
from .core import make_data,train
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--output",default="artifacts/outage.joblib");a=p.parse_args();Path(a.output).parent.mkdir(parents=True,exist_ok=True);x,y,_=make_data();joblib.dump(train(x,y),a.output)
