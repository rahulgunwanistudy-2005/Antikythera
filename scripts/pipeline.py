"""Resumable project build. Default is cached/offline and never calls paid models."""
import argparse
import json
from pathlib import Path
from scripts.build_dataset import ROOT


def run(root=ROOT,collect=True):
    root=Path(root)
    if collect:
        from scripts.collect import collect as collect_data
        manifest=json.loads((root/'data/raw/sources.json').read_text())['sources']
        needed=[root/s['local_text_path'] for s in manifest if s.get('layer') in ('dioscorides','byzantine','renaissance','balkan') and s.get('local_text_path')]
        if all(path.exists() for path in needed) or not (root/'data/derived/claims_proposed.json').exists():
            collect_data(root=root,fetch=False)
        else:
            from scripts.snapshot import verify_snapshot
            verify_snapshot(root)
            print('Using the bundled source-grounded proposal snapshot; fetch source files before local source review.')
    from scripts.suggest_evidence import run as suggest_evidence
    suggest_evidence(root)
    from scripts.snapshot import write_snapshot
    write_snapshot(root)
    from scripts.sync_repository import sync
    from scripts.promote import promote
    from scripts.report import generate
    from scripts.workspace import export
    repository=sync(root)
    promote(root,repository)
    report=generate(root)
    repository.export_parquet(root/'data/derived/parquet')
    export(root,repository)
    return {'status':'succeeded','scientific_status':report['status'],'headline':report['headline'],'counts':report['readiness']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--skip-collection',action='store_true');a=p.parse_args()
    print(json.dumps(run(collect=not a.skip_collection),indent=2))
