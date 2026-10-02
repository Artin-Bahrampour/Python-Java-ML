import pandas as pd
from app.drift import psi,js_divergence,analyze
def test_psi_detects_shift(): assert psi(pd.Series([10,11,12,13,14,15,16,17,18,19]),pd.Series([30,31,32,33,34,35,36,37,38,39]))>.2
def test_js_detects_shift(): assert js_divergence(pd.Series(["A"]*90+["B"]*10),pd.Series(["A"]*10+["B"]*90))>.1
def test_analyze_marks_drift():
    r=analyze(pd.DataFrame({"x":[1,2,3,4,5],"segment":["A"]*5}),pd.DataFrame({"x":[10,11,12,13,14],"segment":["B"]*5})); assert any(x.drifted for x in r)
