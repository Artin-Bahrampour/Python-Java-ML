from pathlib import Path
import numpy as np
import pandas as pd
def generate(rows=1000,seed=42,drift=False):
    rng=np.random.default_rng(seed); age=rng.normal(38,10,rows); income=rng.lognormal(10.5,.45,rows); region=rng.choice(["NO","SE","DK","FI"],rows,p=[.5,.2,.15,.15])
    if drift: age+=7; income*=1.25; region=rng.choice(["NO","SE","DK","FI"],rows,p=[.2,.2,.2,.4])
    return pd.DataFrame({"age":age.round(1),"income":income.round(2),"region":region})
def write_demo(path,rows=1000,seed=42,drift=False):
    Path(path).parent.mkdir(parents=True,exist_ok=True); generate(rows,seed,drift).to_csv(path,index=False)
