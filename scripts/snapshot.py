"""Verify the versioned proposal export when raw caches are not present in a clone."""
import argparse,hashlib,json
from pathlib import Path
from scripts.build_dataset import ROOT
FILES=('claims_proposed.json','evidence_proposed.json','taxa_proposed.json','effort_proposed.json','collection.json','offline_evidence_suggestions.json')

def write_snapshot(root=ROOT):
    root=Path(root);files={name:hashlib.sha256((root/'data/derived'/name).read_bytes()).hexdigest() for name in FILES if (root/'data/derived'/name).exists()}
    value={'schema_version':1,'status':'unreviewed_source_grounded_snapshot','files':files,'notice':'Checksums verify bundled proposal integrity, not historical or experimental truth. Source-text review requires the separately acquired raw files.'}
    (root/'data/derived/snapshot_manifest.json').write_text(json.dumps(value,indent=2)+'\n');return value

def verify_snapshot(root=ROOT):
    root=Path(root);path=root/'data/derived/snapshot_manifest.json'
    if not path.exists():raise ValueError('Snapshot manifest is missing; fetch source caches or regenerate a verified local snapshot.')
    data=json.loads(path.read_text())
    for name,expected in data['files'].items():
        if name not in FILES:raise ValueError('Unexpected snapshot path')
        if hashlib.sha256((root/'data/derived'/name).read_bytes()).hexdigest()!=expected:raise ValueError('Snapshot checksum mismatch for '+name)
    return {'status':'verified','files':len(data['files'])}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();print(json.dumps(write_snapshot() if a.write else verify_snapshot(),indent=2))
