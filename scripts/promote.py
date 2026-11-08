"""Export only fully qualified human-reviewed records for scientific ingestion.

Partial span reviews stay in the repository, with a reason they cannot yet enter
analysis. Existing manually reviewed input files are preserved by ID.
"""
import hashlib
import json
from pathlib import Path
from storage.repository import Repository
from storage.review import checked_path
from scripts.build_dataset import ROOT


def unique(rows,key):
    values={}
    for row in rows:values[key(row)]=row
    return [values[k] for k in sorted(values)]


def promote(root=ROOT,repository=None):
    root=Path(root);repository=repository or Repository(root/'data/local/antikythera.duckdb')
    folder=root/'data/reviewed';folder.mkdir(parents=True,exist_ok=True)
    existing={n:json.loads((folder/(n+'.json')).read_text()) if (folder/(n+'.json')).exists() else [] for n in ('claims','identities','taxa','grades','effort')}
    manual={n:[r for r in rows if r.get('review_origin')!='repository'] for n,rows in existing.items()}
    blockers=[];added={n:[] for n in existing}
    def blocked(row,reason):blockers.append({'kind':row['kind'],'id':row['id'],'reason':reason})
    for r in repository.list(status='accept'):
        row={k:v for k,v in r.items() if k not in ('kind','proposal_hash','revision','review_status')}
        if r['kind']=='identity':
            if not row.get('reviewer') or type(row.get('available_year')) is not int or not row.get('source_url'):blocked(r,'Identity provenance is incomplete');continue
            added['identities'].append(row)
        elif r['kind']=='taxon':added['taxa'].append(row)
    taxon_ids={r['species_id'] for r in manual['taxa']+added['taxa']}
    eligible_priors=[]
    for prior in added['identities']:
        if any(c['species_id'] not in taxon_ids for c in prior.get('candidates',[])):
            blockers.append({'kind':'identity','id':prior['id'],'reason':'Candidate taxa require reviewed taxonomy'});continue
        eligible_priors.append(prior)
    added['identities']=eligible_priors
    prior_ids={r['id'] for r in manual['identities']+added['identities']}
    for r in repository.list(status='accept'):
        row={k:v for k,v in r.items() if k not in ('kind','proposal_hash','revision','review_status')}
        if r['kind']=='claim':
            if type(row.get('year')) is not int or row.get('historical_date_reviewed') is not True:blocked(r,'Historical date review is incomplete');continue
            if row.get('licence_reviewed') is not True:blocked(r,'Licence review is incomplete');continue
            if row.get('identity_id') not in prior_ids:blocked(r,'Reviewed identity distribution is missing');continue
            added['claims'].append(row)
        elif r['kind']=='evidence':
            if row.get('species_id') not in taxon_ids:blocked(r,'Reviewed taxonomy is missing');continue
            if row.get('study_type')!='original':blocked(r,'Only original studies enter the confirmation ledger');continue
            added['grades'].append(row)
        elif r['kind']=='effort':
            if not row.get('coverage_reviewed') or row.get('species_id') not in taxon_ids:blocked(r,'Research coverage or taxonomy review is incomplete');continue
            added['effort'].append(row)
    keys={'claims':lambda r:r['id'],'identities':lambda r:r['id'],'taxa':lambda r:r['species_id'],'grades':lambda r:(str(r['pmid']),r['species_id'],r['category']),'effort':lambda r:(r['species_id'],r['year'])}
    # Rejected/revised repository records must revoke previously exported records.
    # Only repository-owned exports are replaced, preserving manual records.
    for name,rows in added.items():
        manual_rows=manual[name]
        output=unique(manual_rows+[{**r,'review_origin':'repository'} for r in rows],keys[name])
        (folder/(name+'.json')).write_text(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    status={'eligible':{n:len(v) for n,v in added.items()},'blocked_reviews':blockers}
    (root/'data/derived/review_readiness.json').write_text(json.dumps(status,indent=2)+'\n')
    return status

if __name__=='__main__':
    result=promote();print(json.dumps(result,indent=2))
