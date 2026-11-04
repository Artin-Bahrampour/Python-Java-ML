import numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
FEATURES=["price_index","promo_active","stockout_days","recent_week_units","season_index"]
def synthetic(n=4000,seed=1104):
 r=np.random.default_rng(seed);price=r.normal(1,0.12,n).clip(.65,1.5);promo=r.integers(0,2,n);stock=r.poisson(1,n);recent=r.gamma(4,16,n);season=r.uniform(.7,1.35,n);y=(recent*season*(1+.35*promo)-25*(price-1)-2*stock+r.normal(0,8,n)).clip(0)
 return pd.DataFrame({"sku_id":[f"SKU-{i%100:03}" for i in range(n)],"price_index":price,"promo_active":promo,"stockout_days":stock,"recent_week_units":recent,"season_index":season,"next_week_units":y})
def train(df):
 xt,xv,yt,yv=train_test_split(df[FEATURES],df.next_week_units,test_size=.2,random_state=1104)
 models={q:HistGradientBoostingRegressor(loss="quantile",quantile=q,max_iter=220,learning_rate=.07,l2_regularization=.3,random_state=1104).fit(xt,yt) for q in (.1,.5,.9)};lo,mid,hi=(models[q].predict(xv) for q in (.1,.5,.9));lo,hi=np.minimum(lo,hi),np.maximum(lo,hi)
 return {"models":models,"model_version":"2026.11.04","metrics":{"mae":round(float(mean_absolute_error(yv,mid)),3),"interval_coverage":round(float(((yv>=lo)&(yv<=hi)).mean()),4),"validation_rows":len(yv)}},None
