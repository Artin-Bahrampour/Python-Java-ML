import joblib
from pathlib import Path
from .core import data,fit
if __name__=="__main__":
 Path("artifacts").mkdir(exist_ok=True);joblib.dump(fit(*data()),"artifacts/fraud.joblib")
