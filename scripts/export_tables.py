"""Typed Parquet exports of the actual validated cohort, including empty schemas."""
import json
from pathlib import Path
import duckdb
from scripts.build_dataset import ROOT

def export_tables(dataset,root=ROOT):
    out=Path(root)/'data/derived';out.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect()
    try:
        con.execute('CREATE TABLE claims (id VARCHAR,identity_group VARCHAR,category VARCHAR,year INTEGER,identity_available_year INTEGER,layer VARCHAR,candidates_json VARCHAR)')
        rows=[[c['id'],c['identity_group'],c['category'],c['year'],c['identity_available_year'],c['layer'],json.dumps(c['candidates'],sort_keys=True)] for c in dataset['claims']]
        if rows:con.executemany('INSERT INTO claims VALUES (?,?,?,?,?,?,?)',rows)
        con.execute('CREATE TABLE ledger (species VARCHAR,category VARCHAR,tested_year INTEGER,confirmed_year INTEGER,refuted_year INTEGER,in_vitro_confirmed_year INTEGER,pmids_json VARCHAR)')
        rows=[[r['species'],r['category'],r['tested_year'],r.get('confirmed_year'),r.get('refuted_year'),r.get('in_vitro_confirmed_year'),json.dumps(r.get('pmids',[]))] for r in dataset['ledger']]
        if rows:con.executemany('INSERT INTO ledger VALUES (?,?,?,?,?,?,?)',rows)
        con.execute('COPY claims TO $destination (FORMAT PARQUET)',{'destination':str(out/'claims.parquet')})
        con.execute('COPY ledger TO $destination (FORMAT PARQUET)',{'destination':str(out/'ledger.parquet')})
    finally:con.close()
    return {'claims':len(dataset['claims']),'ledger':len(dataset['ledger'])}
