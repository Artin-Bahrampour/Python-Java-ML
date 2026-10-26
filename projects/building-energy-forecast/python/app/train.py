import argparse
from pathlib import Path
import joblib,numpy as np,pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error
from sklearn.model_selection import train_test_split

FEATURES=["hour","day_of_week","outside_temp_c","occupancy_ratio","prior_hour_kwh"]
def synthetic(rows=5000,seed=101):
 r=np.random.default_rng(seed); h=r.integers(0,24,rows); d=r.integers(0,7,rows); temp=r.normal(9,10,rows).clip(-20,35); occ=r.beta(2,2,rows); prior=r.normal(130,30,rows).clip(20,300)
 load=35+35*occ+2.5*np.maximum(18-temp,0)+1.8*np.maximum(temp-23,0)+25*((h>=8)&(h<=18))+10*(d<5)+.45*prior+r.normal(0,7,rows)
 return pd.DataFrame({"building_id":[f"B-{i%30:02}" for i in range(rows)],"hour":h,"day_of_week":d,"outside_temp_c":temp,"occupancy_ratio":occ,"prior_hour_kwh":prior,"target_kwh":load.clip(0).round(3)})
def train(frame):
 xtr,xv,ytr,yv=train_test_split(frame[FEATURES],frame.target_kwh,test_size=.2,random_state=101)
 model=HistGradientBoostingRegressor(max_iter=220,learning_rate=.08,l2_regularization=.3,random_state=101).fit(xtr,ytr); p=model.predict(xv)
 metrics={"validation_mae_kwh":round(float(mean_absolute_error(yv,p)),3),"validation_rmse_kwh":round(float(mean_squared_error(yv,p)**.5),3),"validation_rows":len(yv)}
 return {"model":model,"model_version":"2026.10.26","metrics":metrics},metrics
def main():
 p=argparse.ArgumentParser();p.add_argument("--synthetic",action="store_true");p.add_argument("--input");p.add_argument("--output",default="artifacts/energy.joblib");a=p.parse_args()
 if bool(a.input)==a.synthetic:p.error("choose exactly one of --input or --synthetic")
 b,m=train(synthetic() if a.synthetic else pd.read_csv(a.input));o=Path(a.output);o.parent.mkdir(parents=True,exist_ok=True);joblib.dump(b,o);print(m)
if __name__=="__main__":main()
