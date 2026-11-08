"""Import collected proposals idempotently into the local DuckDB review store."""
import json
from pathlib import Path
from storage.repository import Repository
from scripts.build_dataset import ROOT

FILES={'claim':'claims_proposed.json','evidence':'evidence_proposed.json','taxon':'taxa_proposed.json','effort':'effort_proposed.json','identity':'identities_proposed.json'}

def sync(root=ROOT,repository=None):
    root=Path(root);repository=repository or Repository(root/'data/local/antikythera.duckdb')
    results={}
    for kind,name in FILES.items():
        path=root/'data/derived'/name
        data=json.loads(path.read_text()) if path.exists() else []
        if isinstance(data,dict):data=data.get('records',data.get(kind+'s',[]))
        records={row['id']:row for row in data}
        model_name={'claim':'model_claims_proposed.json','evidence':'model_evidence_proposed.json'}.get(kind)
        model_path=root/'data/derived'/(model_name or '_no_model_')
        if model_name and model_path.exists():
            for row in json.loads(model_path.read_text()):records[row['id']]=row
        if kind=='evidence':
            suggestion_path=root/'data/derived/offline_evidence_suggestions.json'
            if suggestion_path.exists():
                for suggestion in json.loads(suggestion_path.read_text()):
                    if suggestion['id'] in records:
                        base=records[suggestion['id']]
                        if suggestion.get('record_sha256')==base.get('record_sha256'):
                            records[suggestion['id']]={**base,'offline_suggestion':suggestion.get('suggested_fields',{})}
        if kind=='claim':
            adjudicated=root/'data/derived/model_harmonisation_proposed.json'
            if adjudicated.exists():
                for row in json.loads(adjudicated.read_text()):
                    if row.get('claim_id') in records and row.get('abstain') is False:
                        base=records[row['claim_id']]
                        records[row['claim_id']]={**base,'category':row['category'],'model_rationale':row.get('rationale'),'harmonisation_method':'structured_model_pending_review'}
        if records:results[kind]=repository.sync(kind,list(records.values()))
    path=root/'data/derived/collection.json'
    if path.exists():repository.set_metadata('collection',json.loads(path.read_text()))
    print('Proposal import: '+', '.join(f'{k} {v["total_imported"]}' for k,v in results.items()))
    return repository

if __name__=='__main__':sync()
