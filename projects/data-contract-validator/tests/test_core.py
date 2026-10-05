from pathlib import Path
from dcv.core import validate, load_contract, read_csv

def test_valid_dataset():
    rows=read_csv(Path("examples/customers.csv")); c=load_contract(Path("examples/customers.contract.yaml"))
    r=validate(rows,c,"customers.csv","customers.contract.yaml")
    assert r.passed and r.rows==3

def test_duplicate_unique_value_fails():
    rows=[{"customer_id":"1","email":"a@example.com","country":"NO","age":"20"},{"customer_id":"1","email":"b@example.com","country":"NO","age":"21"}]
    c={"columns":{"customer_id":{"type":"string","unique":True},"email":{"type":"email"},"country":{"type":"string"},"age":{"type":"integer"}}}
    r=validate(rows,c,"x.csv","x.yaml")
    assert not r.passed and any(c.check=="unique:customer_id" and not c.passed for c in r.checks)

def test_invalid_email_fails():
    rows=[{"customer_id":"1","email":"not-an-email","country":"NO","age":"20"}]
    c={"columns":{"customer_id":{"type":"string"},"email":{"type":"email"},"country":{"type":"string"},"age":{"type":"integer"}}}
    assert not validate(rows,c,"x.csv","x.yaml").passed
