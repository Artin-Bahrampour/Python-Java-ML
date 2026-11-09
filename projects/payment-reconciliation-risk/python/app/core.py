import numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,precision_score,recall_score
from sklearn.model_selection import train_test_split
F=["amount","age_hours","currency_mismatch","reference_similarity","counterparty_risk"]
def synthetic(n=4500,seed=1109):
 r=np.random.default_rng(seed);a=r.lognormal(5,.8,n);age=r.gamma(2,5,n);cur=r.binomial(1,.03,n);sim=r.beta(12,2,n);risk=r.beta(2,8,n);y=r.binomial(1,1/(1+np.exp(-(-6+.002*a+.08*age+3*cur-5*sim+3*risk))))
 return pd.DataFrame({"payment_id":[f"P-{i:06}" for i in range(n)],"amount":a,"age_hours":age,"currency_mismatch":cur,"reference_similarity":sim,"counterparty_risk":risk,"needs_review":y})
def train(df):
 xt,xv,yt,yv=train_test_split(df[F],df.needs_review,test_size=.2,random_state=1109,stratify=df.needs_review);m=HistGradientBoostingClassifier(max_iter=250,learning_rate=.06,l2_regularization=.5,random_state=1109).fit(xt,yt);p=m.predict_proba(xv)[:,1];ts=np.arange(.1,.91,.01);good=[t for t in ts if precision_score(yv,p>=t,zero_division=0)>=.4];t=float(max(good or list(ts),key=lambda x:recall_score(yv,p>=x,zero_division=0)))
 return {"model":m,"threshold":t,"model_version":"2026.11.09","metrics":{"ap":round(float(average_precision_score(yv,p)),4),"precision":round(float(precision_score(yv,p>=t,zero_division=0)),4),"recall":round(float(recall_score(yv,p>=t,zero_division=0)),4)}},None
