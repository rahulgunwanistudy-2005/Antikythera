"""Independent gold audit scoring. Empty templates never count as completed work."""
import argparse
import json
import random
from collections import Counter,defaultdict
from pathlib import Path
from audit.metrics import precision_recall,wilson
from identity.calibration import reliability

TASKS=('extraction','harmonisation','abstracts','identity')

def valid(row):
    return (row.get('task') in TASKS and row.get('attested') is True and row.get('independent') is True and isinstance(row.get('reviewer'),str) and len(row['reviewer'].strip())>=2 and row.get('gold') is not None and row.get('prediction') is not None)

def score(rows):
    result={'status':'pending','completed':{},'tasks':{},'excluded':0}
    grouped=defaultdict(list);seen=set()
    for row in rows:
        if not valid(row):result['excluded']+=1;continue
        key=(row['task'],row.get('item_id'))
        if key in seen:raise ValueError('Duplicate audit item; adjudicate disagreements before scoring')
        seen.add(key);grouped[row['task']].append(row)
    for task in TASKS:
        items=grouped[task];result['completed'][task]=len(items)
        if not items:result['tasks'][task]={'n':0,'status':'pending'};continue
        if task=='extraction':
            tp=fp=fn=0;passages=set();recall_complete=True
            for row in items:
                gold=row['gold'];correct=gold.get('correct')
                if type(correct) is not bool:raise ValueError('Extraction gold needs boolean correct')
                tp+=int(correct);fp+=int(not correct)
                passage=gold.get('passage_id')
                if not passage or gold.get('complete_passage_annotation') is not True or type(gold.get('missed_claims')) is not int:
                    recall_complete=False;continue
                if passage not in passages:
                    if gold['missed_claims']<0:raise ValueError('missed_claims must be nonnegative')
                    fn+=gold['missed_claims'];passages.add(passage)
            metrics=precision_recall(tp,fp,fn)
            if not recall_complete:metrics['recall']={'estimate':None,'low':None,'high':None,'n':0,'reason':'Independent complete-passage annotations required for recall'}
            result['tasks'][task]={'status':'scored','n':len(items),'tp':tp,'fp':fp,'fn':fn if recall_complete else None,**metrics}
        elif task in ('harmonisation','abstracts'):
            field='category' if task=='harmonisation' else 'verdict'
            gold=[r['gold'].get(field) for r in items];pred=[r['prediction'].get(field) for r in items]
            if any(not isinstance(v,str) or not v for v in gold+pred):raise ValueError('Gold/prediction labels required')
            labels=sorted(set(gold+pred));classes={}
            for label in labels:
                tp=sum(g==p==label for g,p in zip(gold,pred));fp=sum(g!=label and p==label for g,p in zip(gold,pred));fn=sum(g==label and p!=label for g,p in zip(gold,pred))
                classes[label]=precision_recall(tp,fp,fn)
            metrics={'status':'scored','n':len(items),'accuracy':wilson(sum(g==p for g,p in zip(gold,pred)),len(items)),'classes':classes,'confusion':[{'gold':g,'predicted':p,'n':n} for (g,p),n in sorted(Counter(zip(gold,pred)).items())]}
            if task=='abstracts':
                both=[r for r in items if r['gold'].get('evidence_tier') and r['prediction'].get('evidence_tier')]
                metrics['tier_accuracy']=wilson(sum(r['gold']['evidence_tier']==r['prediction']['evidence_tier'] for r in both),len(both))
            result['tasks'][task]=metrics
        else:
            confidences=[];outcomes=[]
            for row in items:
                p=row['prediction'].get('probability');predicted=row['prediction'].get('species_id');gold=row['gold'].get('species_id')
                if p is None or not predicted or not gold:raise ValueError('Identity audit requires gold species and numeric top-candidate probability')
                confidences.append(p);outcomes.append(int(predicted==gold))
            result['tasks'][task]={'status':'scored',**reliability(confidences,outcomes)}
    if any(result['completed'].values()):result['status']='partially_scored'
    targets={'extraction':200,'harmonisation':150,'abstracts':300}
    result['targets']=targets
    result['targets_met']=all(result['completed'].get(k,0)>=v for k,v in targets.items()) and result['completed'].get('identity',0)>0 and result['tasks'].get('extraction',{}).get('recall',{}).get('estimate') is not None
    return result


def stratified_sample(records,size=200,seed=1729):
    if type(size) is not int or size<0:raise ValueError('Nonnegative sample size required')
    groups=defaultdict(list)
    for row in records:groups[(row.get('era'),row.get('category'),row.get('language','unknown'))].append(row)
    rng=random.Random(seed)
    for rows in groups.values():rng.shuffle(rows)
    keys=sorted(groups,key=str);result=[]
    while keys and len(result)<size:
        for key in list(keys):
            if len(result)>=size:break
            if groups[key]:result.append(groups[key].pop())
            if not groups[key]:keys.remove(key)
    return result


def sample_files(root,size=200):
    root=Path(root);path=root/'data/derived/claims_proposed.json'
    claims=json.loads(path.read_text()) if path.exists() else []
    if isinstance(claims,dict):claims=claims.get('records',[])
    sample=stratified_sample(claims,size)
    out=root/'audit/samples';out.mkdir(parents=True,exist_ok=True)
    records=[{'task':'extraction','item_id':r['id'],'source':{k:r.get(k) for k in ('source_id','source_url','span_start','span_end','source_span','plant_name_as_written','ailment_as_written','category','era')},'prediction':{'category':r.get('category'),'method':r.get('method')},'gold':None,'reviewer':None,'independent':False,'attested':False} for r in sample]
    (out/'extraction.json').write_text(json.dumps(records,indent=2,ensure_ascii=False)+'\n')
    mappings=stratified_sample(claims,150)
    (out/'harmonisation.json').write_text(json.dumps([{'task':'harmonisation','item_id':r['id'],'source':{k:r.get(k) for k in ('source_id','source_url','source_span','ailment_as_written')},'prediction':{'category':r['category']},'gold':None,'reviewer':None,'independent':False,'attested':False} for r in mappings],indent=2,ensure_ascii=False)+'\n')
    evidence_path=root/'data/derived/evidence_proposed.json'
    evidence=json.loads(evidence_path.read_text()) if evidence_path.exists() else []
    selected=stratified_sample(evidence,300)
    (out/'abstracts.json').write_text(json.dumps([{'task':'abstracts','item_id':r['id'],'source':{k:r.get(k) for k in ('pmid','species_id','category','source_url','record_path','record_sha256')},'prediction':{'verdict':r.get('verdict'),'evidence_tier':r.get('evidence_tier')},'gold':None,'reviewer':None,'independent':False,'attested':False} for r in selected],indent=2,ensure_ascii=False)+'\n')
    return {'sampled_extraction':len(sample),'sampled_harmonisation':len(mappings),'sampled_abstracts':len(selected),'completed_audits':0,'seed':1729}


if __name__=='__main__':
    from scripts.build_dataset import ROOT
    p=argparse.ArgumentParser();p.add_argument('--sample',action='store_true');p.add_argument('--input',type=Path,default=ROOT/'data/reviewed/audits.json');a=p.parse_args()
    if a.sample:print(json.dumps(sample_files(ROOT)))
    else:print(json.dumps(score(json.loads(a.input.read_text()) if a.input.exists() else []),indent=2))
