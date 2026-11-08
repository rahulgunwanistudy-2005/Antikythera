"""One data contract for the local workspace and private static snapshot."""
import json
from pathlib import Path
from scripts.build_dataset import ROOT
from storage.repository import Repository


def read(path,default):
    return json.loads(path.read_text()) if path.exists() else default


def workspace(root=ROOT,repository=None,mode='static'):
    root=Path(root);derived=root/'data/derived';reviewed=root/'data/reviewed'
    catalog=read(root/'data/seed/catalog.json',{'plants':[],'categories':[]})
    dataset=read(derived/'dataset.json',{'claims':[],'ledger':[],'taxa':[],'effort':[]})
    report=read(derived/'report.json',{})
    sources=read(root/'data/raw/sources.json',{'sources':[]})['sources']
    proposals={}
    files={'claim':'claims_proposed.json','evidence':'evidence_proposed.json','taxon':'taxa_proposed.json','identity':'identities_proposed.json','effort':'effort_proposed.json'}
    for kind,name in files.items():
        if repository is not None:records=repository.list(kind=kind)
        else:
            records=read(derived/name,[])
            if isinstance(records,dict):records=records.get('records',[])
            records=[{**r,'revision':0,'review_status':'pending'} for r in records]
        # Abstracts and full retrieved records remain local, whatever upstream file contains.
        proposals[kind]=[{k:v for k,v in r.items() if k not in ('abstract','full_text','api_key','record_path')} for r in records]
    identities=read(reviewed/'identities.json',[])
    raw_claims=read(reviewed/'claims.json',[])
    provenance={r['id']:r for r in raw_claims}
    claims=[{**provenance.get(r['id'],{}),**r} for r in dataset.get('claims',[])]
    collection=read(derived/'collection.json',{'status':'not_collected','counts':{},'limitations':[]})
    model=read(derived/'ranker.json',{'status':'pending','reason':'No trained model artifact yet.'})
    # Model text can be megabytes; the UI only needs evaluation, model state and leads.
    model={k:v for k,v in model.items() if k not in ('model_strings','calibrators')}
    shortlist=read(derived/'shortlist.json',{'status':'pending','leads':[]})
    model['forward']=shortlist;model['shortlist']=shortlist.get('leads',[]);model['shortlist_status']=shortlist.get('status');model['shortlist_reason']=shortlist.get('reason')
    result={'schema_version':2,'mode':mode,'sources':sources,'collection':collection,'proposed_claims':proposals['claim'],'proposed_evidence':proposals['evidence'],'proposed_taxa':proposals['taxon'],'proposed_identities':proposals['identity'],'proposed_effort':proposals['effort'],'dataset':dataset,'reviewed':{'claims':claims,'raw_claims':raw_claims,'identities':identities,'ledger':dataset.get('ledger',[]),'taxa':dataset.get('taxa',[]),'grades':[{k:v for k,v in r.items() if k not in ('record_path','reviewer','record_sha256')} for r in read(reviewed/'grades.json',[])]},'ranker':model,'analysis':report.get('analysis',{}),'audits':report.get('audits',{}),'readiness':report.get('readiness',{}),'review_readiness':read(derived/'review_readiness.json',{'blocked_reviews':[]}), 'stats':{'proposed_claims':len(proposals['claim']),'acquired_evidence':len(proposals['evidence']),'reviewed_claims':len(claims),'reviewed_tested_pairs':len(dataset.get('ledger',[]))},'limitations':report.get('limitations',[])}
    if repository is not None:result['review_counts']=repository.counts()
    return result


def export(root=ROOT,repository=None):
    root=Path(root);result=workspace(root,repository)
    path=root/'app/web/public/workspace.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    (root/'data/derived/workspace.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    return result

if __name__=='__main__':
    result=export();print(f'Workspace exported: {result["stats"]}')
