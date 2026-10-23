from app.train import synthetic,train
def test_training_bundle():
    bundle,metrics=train(synthetic(400)); assert .1<=bundle["threshold"]<=.9 and 0<=metrics["average_precision"]<=1
