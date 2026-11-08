import json,tempfile,unittest
from pathlib import Path
from scripts.snapshot import write_snapshot,verify_snapshot
from scripts.pipeline import run

class SnapshotBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        for path in ('data/derived','data/raw','data/reviewed','data/seed'):(self.root/path).mkdir(parents=True)
        proposal={'id':'synthetic-proposal','source_span':'Synthetic source words','reviewed':False}
        for name,body in [('claims_proposed.json',[proposal]),('evidence_proposed.json',[]),('taxa_proposed.json',[]),('effort_proposed.json',[]),('offline_evidence_suggestions.json',[]),('collection.json',{'status':'snapshot','counts':{'proposed_claims':1},'source_status':[]})]:
            (self.root/'data/derived'/name).write_text(json.dumps(body))
        (self.root/'data/raw/sources.json').write_text(json.dumps({'sources':[{'id':'synthetic-source','layer':'renaissance','local_text_path':'data/raw/cache/missing.txt'}]}))
        for name in ('claims','identities','taxa','grades','effort'):(self.root/f'data/reviewed/{name}.json').write_text('[]')
        (self.root/'data/reviewed/coverage.json').write_text('{"observation_end":2026,"search_complete":false,"effort_coverage_complete":false}')
        (self.root/'data/seed/catalog.json').write_text('{"plants":[],"categories":[]}')
        write_snapshot(self.root)
    def test_missing_raw_cache_preserves_snapshot_and_pending_science(self):
        result=run(self.root)
        self.assertEqual(result['status'],'succeeded');self.assertIsNone(result['headline'])
        self.assertEqual(json.loads((self.root/'app/web/public/workspace.json').read_text())['stats']['proposed_claims'],1)
    def test_changed_snapshot_rejected(self):
        (self.root/'data/derived/claims_proposed.json').write_text('[]')
        with self.assertRaisesRegex(ValueError,'checksum mismatch'):verify_snapshot(self.root)
