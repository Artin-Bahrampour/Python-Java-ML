import numpy as np,pandas as pd
from sklearn.ensemble import IsolationForest
FEATURES=["p95_latency_ms","error_rate","requests_per_second","cpu_saturation"]
def synthetic(rows=3500,seed=30):
 r=np.random.default_rng(seed);lat=r.lognormal(4.4,.25,rows);err=r.beta(1,35,rows);rps=r.normal(250,35,rows);cpu=r.beta(3,4,rows);idx=r.choice(rows,rows//18,replace=False);lat[idx]*=r.uniform(2,5,len(idx));err[idx]+=r.uniform(.08,.4,len(idx));cpu[idx]=np.minimum(1,cpu[idx]+.3)
 return pd.DataFrame({"window_id":[f"W-{i:06}" for i in range(rows)],"p95_latency_ms":lat,"error_rate":err,"requests_per_second":rps.clip(1),"cpu_saturation":cpu})
def train(frame):
 x=frame[FEATURES];model=IsolationForest(n_estimators=250,contamination=.05,random_state=30).fit(x);scores=-model.score_samples(x);threshold=float(np.quantile(scores,.95));return {"model":model,"threshold":threshold,"model_version":"2026.10.30","baseline":{k:float(x[k].median()) for k in FEATURES}}, {"training_rows":len(x),"alert_rate":.05}
