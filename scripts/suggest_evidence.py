"""Recompute conservative evidence cues locally; never produce reviewed labels."""
import hashlib,json
from pathlib import Path
from scripts.build_dataset import ROOT
from ledger.offline_grade import suggest
from scripts.collect import dump


def run(root=ROOT):
    root=Path(root);path=root/'data/derived/evidence_proposed.json'
    if not path.exists():return {'status':'no_evidence_queue','suggestions':0}
    evidence=json.loads(path.read_text());old_path=root/'data/derived/offline_evidence_suggestions.json'
    old={r['id']:r for r in json.loads(old_path.read_text())} if old_path.exists() else {}
    rows=[];cached=0
    for row in evidence:
        record=(root/row['record_path']).resolve()
        if not record.is_relative_to(root.resolve()):raise ValueError('Evidence path escapes project')
        if not record.exists():
            previous=old.get(row['id'])
            if previous and previous.get('record_sha256')==row['record_sha256']:rows.append(previous);cached+=1
            continue
        raw=record.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['record_sha256']:raise ValueError('Evidence record changed: '+row['id'])
        result=suggest(json.loads(raw),row['species_id'],row['category'])
        rows.append({'id':row['id'],'suggested_fields':result,'record_sha256':row['record_sha256'],'status':'offline_suggestion_pending_human_review','reviewed':False})
    dump(old_path,rows)
    collection_path=root/'data/derived/collection.json'
    if collection_path.exists():
        collection=json.loads(collection_path.read_text());counts=collection.setdefault('counts',{})
        counts['offline_evidence_suggestions']=len(rows);counts['offline_verdict_abstentions']=sum(r['suggested_fields']['abstain'] for r in rows)
        dump(collection_path,collection)
    return {'status':'suggestions_pending_review','suggestions':len(rows),'cached_snapshot_rows':cached,'reviewed':0}

if __name__=='__main__':print(json.dumps(run(),indent=2))
