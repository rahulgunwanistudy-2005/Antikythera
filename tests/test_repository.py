"""Synthetic review-state and scientific provenance boundaries."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from storage.repository import Repository,Conflict
from storage.review import validate_review

class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.repository=Repository(self.root/'test.duckdb')
    def test_import_cannot_forge_human_review(self):
        self.repository.sync('claim',[{'id':'synthetic','reviewed':True,'reviewer':'forged'}]);r=self.repository.get('claim','synthetic')
        self.assertFalse(r['reviewed']);self.assertIsNone(r['reviewer'])
    def test_revisions_reject_stale_updates(self):
        r=self.repository;r.sync('claim',[{'id':'synthetic'}]);r.review('claim','synthetic','Human fixture','accept','Synthetic testing',0,{},True)
        with self.assertRaises(Conflict):r.review('claim','synthetic','Human fixture','reject','Synthetic stale',0,{},True)
        self.assertEqual(len(r.history()),1)
    def test_changed_proposal_revokes_review_but_preserves_history(self):
        r=self.repository;r.sync('claim',[{'id':'synthetic','text':'A'}]);r.review('claim','synthetic','Human fixture','accept','Synthetic testing',0,{},True)
        r.sync('claim',[{'id':'synthetic','text':'B'}]);row=r.get('claim','synthetic')
        self.assertFalse(row['reviewed']);self.assertEqual(row['revision'],2);self.assertEqual(len(r.history()),2);self.assertTrue(r.verify_trail())
    def test_review_requires_attestation(self):
        self.repository.sync('claim',[{'id':'synthetic'}])
        with self.assertRaises(ValueError):self.repository.review('claim','synthetic','Human fixture','accept','Testing',0,{},False)
    def test_parameterized_queries_do_not_run_user_sql(self):
        self.repository.sync('claim',[{'id':"a'; DROP TABLE records;--"}]);self.assertEqual(len(self.repository.list('claim',query="DROP TABLE")),1)
    def test_source_mismatch_blocks_acceptance(self):
        p=self.root/'source.txt';p.write_text('Altered')
        row={'source_text_path':'source.txt','source_sha256':hashlib.sha256(b'Original').hexdigest()}
        with self.assertRaisesRegex(ValueError,'changed'):validate_review('claim',row,{},self.root)
    def test_parquet_roundtrip_preserves_provenance(self):
        import duckdb
        self.repository.sync('claim',[{'id':'synthetic','source_span':'A test.'}]);path=self.repository.export_parquet(self.root/'parquet')
        with duckdb.connect() as con:row=con.execute('SELECT payload,review_status FROM read_parquet(?)',[str(path/'claims.parquet')]).fetchone()
        self.assertEqual(json.loads(row[0])['source_span'],'A test.');self.assertEqual(row[1],'pending')

class LocalApiReviewTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from app.api.main import create_app
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.app=create_app(self.root,self.root/'test.duckdb');self.client=TestClient(self.app);self.repo=self.app.state.repository
        self.repo.sync('harmonisation',[{'id':'synthetic','category':'urinary'}])
        self.body={'reviewer':'Test human','decision':'accept','note':'Synthetic test only','expected_revision':0,'attested':True,'fields':{'category':'urinary'}}
    def test_valid_review_and_stale_conflict(self):
        self.assertEqual(self.client.post('/api/reviews/harmonisation/synthetic',json=self.body).status_code,200)
        self.assertEqual(self.client.post('/api/reviews/harmonisation/synthetic',json=self.body).status_code,409)
    def test_external_origin_cannot_write_local_reviews(self):
        r=self.client.post('/api/reviews/harmonisation/synthetic',json=self.body,headers={'Origin':'https://unrelated.example'})
        self.assertEqual(r.status_code,403);self.assertEqual(self.repo.get('harmonisation','synthetic')['revision'],0)
    def test_read_only_mode_rejects_review(self):
        from app.api.main import create_app
        from fastapi.testclient import TestClient
        app=create_app(self.root,self.root/'other.duckdb',review_enabled=False)
        self.assertEqual(TestClient(app).post('/api/reviews/harmonisation/synthetic',json=self.body).status_code,403)
    def test_protected_fields_cannot_be_submitted(self):
        body={**self.body,'fields':{'reviewed':True}}
        self.assertEqual(self.client.post('/api/reviews/harmonisation/synthetic',json=body).status_code,422)
