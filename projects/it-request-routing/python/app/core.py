from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

SAMPLES={"access":["reset my password","cannot log into vpn","need access to finance folder","multi factor code not working"],"hardware":["laptop battery is swollen","my monitor does not turn on","keyboard keys are broken","need replacement docking station"],"network":["office wifi is slow","cannot connect to internal network","vpn disconnects every hour","network printer unavailable"],"software":["excel crashes when opening files","install approved design software","browser extension stopped working","update my python environment"]}
def synthetic():
 text=[];labels=[]
 for label,items in SAMPLES.items():
  for i in range(35): text.append(items[i%len(items)]+f" ticket {i}");labels.append(label)
 return text,labels
def train(text,labels):
 xt,xv,yt,yv=train_test_split(text,labels,test_size=.25,random_state=41,stratify=labels)
 pipe=Pipeline([("tfidf",TfidfVectorizer(ngram_range=(1,2),min_df=1,sublinear_tf=True)),("clf",CalibratedClassifierCV(LogisticRegression(max_iter=1000,class_weight="balanced",random_state=41),method="sigmoid",cv=3))]);pipe.fit(xt,yt);pred=pipe.predict(xv)
 return {"pipeline":pipe,"confidence_threshold":.62,"model_version":"2026.11.02","metrics":{"macro_f1":round(float(f1_score(yv,pred,average="macro")),4),"validation_rows":len(yv)}},None
