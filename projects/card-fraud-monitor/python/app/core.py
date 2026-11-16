import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score,roc_auc_score
F=["amount","hour","merchant_risk","velocity_1h","international","card_age_days"]
def data(n=5000,seed=7):
 r=np.random.default_rng(seed);t=np.arange(n);x=np.c_[r.lognormal(3.8,1,n),r.integers(0,24,n),r.random(n),r.poisson(.6,n),r.binomial(1,.08,n),r.integers(1,4000,n)]
 z=-7+.014*x[:,0]+1.8*x[:,2]+.7*x[:,3]+1.6*x[:,4]-.0005*x[:,5]+.0003*t;y=r.binomial(1,1/(1+np.exp(-z)));return x,y
def fit(x,y):
 k=int(.8*len(y));a,b=x[:k],x[k:];ya,yb=y[:k],y[k:]
 base=LogisticRegression(max_iter=1000,class_weight="balanced").fit(a,ya)
 model=CalibratedClassifierCV(HistGradientBoostingClassifier(max_iter=260,learning_rate=.05,l2_regularization=1,random_state=7),cv=4).fit(a,ya)
 p=model.predict_proba(b)[:,1];grid=np.linspace(.02,.9,89);th=float(grid[np.argmin([2000*np.sum((p<q)&(yb==1))+25*np.sum(p>=q) for q in grid])])
 return {"model":model,"threshold":th,"version":"fraud-2026.11","metrics":{"baseline_ap":round(float(average_precision_score(yb,base.predict_proba(b)[:,1])),3),"model_ap":round(float(average_precision_score(yb,p)),3),"auc":round(float(roc_auc_score(yb,p)),3)},"amount_ref":a[:,0]}
def psi(a,b):
 e=np.quantile(a,np.linspace(0,1,11));e[0],e[-1]=-np.inf,np.inf;x=np.clip(np.histogram(a,e)[0]/len(a),1e-6,None);y=np.clip(np.histogram(b,e)[0]/len(b),1e-6,None);return float(np.sum((y-x)*np.log(y/x)))
