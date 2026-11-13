import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
FEATURES=["signal_drop_db","packet_loss_pct","latency_ms","weather_severity","site_age_years","alarms_6h"]
def make_data(n=3600,seed=41):
 r=np.random.default_rng(seed);t=np.arange(n);x=np.c_[r.normal(5,2,n),r.gamma(1.8,1.3,n),r.normal(35,12,n),r.integers(0,4,n),r.integers(0,25,n),r.poisson(.7,n)].clip(0)
 y=r.binomial(1,1/(1+np.exp(-(-6+.35*x[:,0]+.38*x[:,1]+.025*x[:,2]+.5*x[:,3]+.55*x[:,5]+.001*t))));return x,y,t
def psi(a,b,bins=10):
 e=np.quantile(a,np.linspace(0,1,bins+1));e[0],e[-1]=-np.inf,np.inf;x=np.clip(np.histogram(a,e)[0]/len(a),1e-6,None);y=np.clip(np.histogram(b,e)[0]/len(b),1e-6,None);return float(np.sum((y-x)*np.log(y/x)))
def train(x,y):
 c=int(len(y)*.75);xa,ya,xt,yt=x[:c],y[:c],x[c:],y[c:]
 base=LogisticRegression(max_iter=800,class_weight="balanced").fit(xa,ya)
 model=CalibratedClassifierCV(HistGradientBoostingClassifier(max_iter=220,learning_rate=.06,l2_regularization=.6,random_state=41),method="sigmoid",cv=4).fit(xa,ya)
 p=model.predict_proba(xt)[:,1];g=np.linspace(.05,.95,91);q=float(g[np.argmin([800*np.sum((p<v)&(yt==1))+120*np.sum(p>=v) for v in g])])
 return {"model":model,"threshold":q,"metrics":{"baseline_ap":round(float(average_precision_score(yt,base.predict_proba(xt)[:,1])),3),"model_ap":round(float(average_precision_score(yt,p)),3),"brier":round(float(brier_score_loss(yt,p)),3),"validation_positive_rate":round(float(yt.mean()),3)},"reference_signal":xa[:,0],"version":"outage-2026.11"}
