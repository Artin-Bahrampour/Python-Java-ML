from app.train import synthetic,train
def test_train():
 b,m=train(synthetic(500));assert m["validation_mae_kwh"]>=0 and b["model_version"]
