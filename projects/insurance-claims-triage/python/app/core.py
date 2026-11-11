from __future__ import annotations
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve

FEATURES = ["claim_amount", "policy_age_days", "prior_claims", "incident_delay_days", "risk_region"]

def sample(n: int = 2400, seed: int = 11):
    rng=np.random.default_rng(seed)
    x=np.column_stack([rng.lognormal(8.1, .8,n), rng.integers(1,3000,n), rng.poisson(.7,n), rng.integers(0,90,n), rng.integers(0,2,n)]).astype(float)
    logits=-6 + .00011*x[:,0] - .001*x[:,1] + .7*x[:,2] + .035*x[:,3] + .9*x[:,4]
    y=rng.binomial(1,1/(1+np.exp(-logits)))
    return x,y

def fit(x,y):
    model=HistGradientBoostingClassifier(max_iter=180, learning_rate=.07, l2_regularization=.4, random_state=11).fit(x,y)
    p=model.predict_proba(x)[:,1]; precision, recall, thresholds=precision_recall_curve(y,p)
    # Review policy: choose highest recall threshold that keeps alert precision >= 45%.
    choices=np.where(precision[:-1] >= .45)[0]
    threshold=float(thresholds[choices[np.argmax(recall[:-1][choices])]]) if len(choices) else .5
    return {"model":model,"threshold":threshold,"metrics":{"average_precision":round(float(average_precision_score(y,p)),3),"positive_rate":round(float(y.mean()),3)},"version":"claims-v1"}
