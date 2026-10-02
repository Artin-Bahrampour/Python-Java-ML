import argparse,json
from pathlib import Path
import pandas as pd
from app.db import init_db,SessionLocal
from app.service import DriftService
from app.data_generator import write_demo
def main():
    p=argparse.ArgumentParser(); s=p.add_subparsers(dest="cmd",required=True)
    d=s.add_parser("demo"); d.add_argument("--rows",type=int,default=1000); d.add_argument("--seed",type=int,default=42)
    a=s.add_parser("analyze"); a.add_argument("--reference",required=True); a.add_argument("--current",required=True)
    e=s.add_parser("export"); e.add_argument("--report-id",type=int,required=True); e.add_argument("--output",required=True)
    x=p.parse_args(); init_db()
    if x.cmd=="demo": write_demo("data/reference.csv",x.rows,x.seed); write_demo("data/current.csv",x.rows,x.seed+1,True); print("Generated demo datasets")
    elif x.cmd=="analyze":
        with SessionLocal() as db: r,f=DriftService(db).run(pd.read_csv(x.reference).to_dict("records"),pd.read_csv(x.current).to_dict("records")); print(json.dumps({"report_id":r.id,"features":f},indent=2))
    else:
        with SessionLocal() as db:
            r=DriftService(db).get(x.report_id)
            if not r: raise SystemExit("Report not found")
            Path(x.output).write_text(json.dumps({"id":r.id,"features":json.loads(r.summary_json)},indent=2)); print(x.output)
if __name__=="__main__": main()
