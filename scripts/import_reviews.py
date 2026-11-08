"""Validate a locally exported review batch; apply only with an explicit flag."""
import argparse,json
from pathlib import Path
from scripts.build_dataset import ROOT
from storage.repository import Repository,Conflict
from storage.review import validate_review


def import_batch(value,root=ROOT,repository=None,apply=False):
    root=Path(root);repository=repository or Repository(root/'data/local/antikythera.duckdb')
    rows=value.get('reviews',[value]) if isinstance(value,dict) else value
    if not isinstance(rows,list) or not rows:raise ValueError('A nonempty review batch is required')
    prepared=[];seen=set()
    for row in rows:
        kind=row['kind'];id_=row['record_id'];key=(kind,id_)
        if key in seen:raise ValueError('A batch may contain each record only once')
        seen.add(key);current=repository.get(kind,id_)
        if current['revision']!=row['expected_revision']:raise Conflict('Batch revision is stale for '+id_)
        if row.get('attested') is not True or not row.get('reviewer','').strip() or not row.get('note','').strip():raise ValueError('Reviewer, evidence note and explicit personal attestation are required')
        fields=validate_review(kind,current,row.get('fields',{}),root,row['decision'])
        prepared.append((kind,id_,row,fields))
    if apply:
        for kind,id_,row,fields in prepared:repository.review(kind,id_,row['reviewer'],row['decision'],row['note'],row['expected_revision'],fields,True)
    return {'status':'applied' if apply else 'validated_not_applied','records':len(prepared),'next_step':'Run make report after applying a batch. Scientific eligibility is checked independently.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('file',type=Path);p.add_argument('--apply',action='store_true');a=p.parse_args()
    print(json.dumps(import_batch(json.loads(a.file.read_text()),apply=a.apply),indent=2))
