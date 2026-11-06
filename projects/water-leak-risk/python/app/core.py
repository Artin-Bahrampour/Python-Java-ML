import numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,roc_auc_score
from sklearn.model_selection import train_test_split
F=["pressure_drop_bar","flow_cv","pipe_age_years","repairs_5y","soil_risk"]
def synthetic(n=3500,seed=1106):
 r=np.random.default_rng(seed);p=r.gamma(2,.12,n);f=r.beta(2,8,n);a=r.gamma(4,10,n);rep=r.poisson(.6,n);s=r.beta(2,3,n);y=r.binomial(1,1/(1+np.exp(-(-5+4*p+3*f+.035*a+.5*rep+1.2*s))))
 return pd.DataFrame({"segment_id":[f"SEG-{i:05}" for i in range(n)],"pressure_drop_bar":p,"flow_cv":f,"pipe_age_years":a,"repairs_5y":rep,"soil_risk":s,"leak_30d":y})
def train(df):
 xtr,xv,ytr,yv=train_test_split(df[F],df.leak_30d,test_size=.2,random_state=1106,stratify=df.leak_30d);m=HistGradientBoostingClassifier(max_iter=220,learning_rate=.07,random_state=1106).fit(xtr,ytr);p=m.predict_proba(xv)[:,1];return {"model":m,"threshold":.5,"model_version":"2026.11.06","metrics":{"auc":round(float(roc_auc_score(yv,p)),4),"ap":round(float(average_precision_score(yv,p)),4)}},None
