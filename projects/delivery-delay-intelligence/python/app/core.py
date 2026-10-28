import numpy as np,pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score,roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
FEATURES=["carrier","route_km","package_kg","weather_risk","weekday","hub_backlog"]
def synthetic(rows=4000,seed=28):
 r=np.random.default_rng(seed);carrier=r.choice(["road","air","sea"],rows,p=[.72,.18,.1]);route=r.gamma(3,120,rows);kg=r.gamma(2,3,rows);weather=r.beta(2,7,rows);weekday=r.integers(0,7,rows);backlog=r.gamma(3,12,rows)
 logit=-4+.002*route+.05*kg+2.8*weather+.035*backlog+.35*(carrier=="sea")+.15*(weekday==0);y=r.binomial(1,1/(1+np.exp(-logit)))
 return pd.DataFrame({"shipment_id":[f"S-{i:06}" for i in range(rows)],"carrier":carrier,"route_km":route,"package_kg":kg,"weather_risk":weather,"weekday":weekday,"hub_backlog":backlog,"delayed":y})
def train(frame):
 xt,xv,yt,yv=train_test_split(frame[FEATURES],frame.delayed,test_size=.2,random_state=28,stratify=frame.delayed)
 prep=ColumnTransformer([("cat",OneHotEncoder(handle_unknown="ignore",sparse_output=False),["carrier"]),("num",SimpleImputer(strategy="median"),FEATURES[1:])]);pipe=Pipeline([("prep",prep),("clf",HistGradientBoostingClassifier(max_iter=200,learning_rate=.08,random_state=28))]).fit(xt,yt);p=pipe.predict_proba(xv)[:,1]
 metrics={"auc":round(float(roc_auc_score(yv,p)),4),"average_precision":round(float(average_precision_score(yv,p)),4),"validation_rows":len(yv)}
 baseline={k:float(frame[k].mean()) for k in FEATURES if k!="carrier"}
 return {"pipeline":pipe,"threshold":.5,"model_version":"2026.10.28","metrics":metrics,"baseline":baseline},metrics
