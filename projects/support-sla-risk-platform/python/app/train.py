import argparse
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES=["priority","channel","age_minutes","messages_count","customer_tier","agent_queue_depth"]

def synthetic(rows=2500, seed=19):
    r=np.random.default_rng(seed); priority=r.choice(["low","normal","high","urgent"],rows,p=[.18,.52,.23,.07]); channel=r.choice(["email","chat","phone"],rows,p=[.48,.38,.14]); tier=r.choice(["standard","business","enterprise"],rows,p=[.7,.22,.08]); age=r.gamma(2.3,50,rows).clip(0,1500).astype(int); messages=r.poisson(3,rows); queue=r.gamma(3,7,rows).clip(0,100).astype(int)
    logit=-4+.006*age+.045*queue+.12*messages+1.1*(priority=="urgent")+.55*(priority=="high")+.25*(channel=="email")
    label=r.binomial(1,1/(1+np.exp(-logit)))
    return pd.DataFrame({"ticket_id":[f"T-{i:05d}" for i in range(rows)],"priority":priority,"channel":channel,"age_minutes":age,"messages_count":messages,"customer_tier":tier,"agent_queue_depth":queue,"breach":label})

def train(frame):
    xt,xv,yt,yv=train_test_split(frame[FEATURES],frame.breach,test_size=.2,random_state=19,stratify=frame.breach)
    prep=ColumnTransformer([("cat",Pipeline([("fill",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore"))]),["priority","channel","customer_tier"]),("num",SimpleImputer(strategy="median"),["age_minutes","messages_count","agent_queue_depth"])])
    pipe=Pipeline([("prep",prep),("model",RandomForestClassifier(n_estimators=220,min_samples_leaf=5,class_weight="balanced",random_state=19,n_jobs=-1))]); pipe.fit(xt,yt); p=pipe.predict_proba(xv)[:,1]
    candidates=np.arange(.1,.91,.01); valid=[t for t in candidates if precision_score(yv,p>=t,zero_division=0)>=.3]; threshold=float(max(valid or list(candidates),key=lambda t:recall_score(yv,p>=t,zero_division=0)))
    metrics={"average_precision":round(float(average_precision_score(yv,p)),4),"recall":round(float(recall_score(yv,p>=threshold)),4),"precision":round(float(precision_score(yv,p>=threshold,zero_division=0)),4)}
    return {"pipeline":pipe,"threshold":threshold,"model_version":"2026.10.23","metrics":metrics},metrics

def main():
    p=argparse.ArgumentParser(); p.add_argument("--synthetic",action="store_true"); p.add_argument("--input"); p.add_argument("--output",default="artifacts/sla.joblib"); a=p.parse_args()
    if bool(a.input)==a.synthetic: p.error("choose exactly one of --input or --synthetic")
    bundle,metrics=train(synthetic() if a.synthetic else pd.read_csv(a.input)); target=Path(a.output); target.parent.mkdir(parents=True,exist_ok=True); joblib.dump(bundle,target); print(metrics)
if __name__=="__main__": main()
