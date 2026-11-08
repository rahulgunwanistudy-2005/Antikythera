import tempfile,unittest
from pathlib import Path
from storage.repository import Repository

class AuditIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.repo=Repository(Path(self.temp.name)/'test.duckdb')
    def test_gold_audit_compares_frozen_prediction_not_corrected_review(self):
        r=self.repo;r.sync('claim',[{'id':'test','category':'gi'}]);r.review('claim','test','Test reviewer','accept','Synthetic correction',0,{'category':'urinary'},True)
        self.assertEqual(r.get('claim','test')['category'],'urinary');self.assertEqual(r.proposal('claim','test')['category'],'gi')
    def test_changed_proposal_invalidates_old_audit_without_erasing_it(self):
        r=self.repo;r.sync('claim',[{'id':'test','category':'gi'}]);row=r.get('claim','test')
        r.add_audit({'kind':'claim','task':'extraction','item_id':'test','reviewer':'Synthetic reviewer','proposal_hash':row['proposal_hash'],'attested':True,'independent':True,'prediction':{'category':'gi'},'gold':{'correct':True}})
        self.assertEqual(len(r.valid_audits()),1);self.assertTrue(r.verify_trail())
        r.sync('claim',[{'id':'test','category':'urinary'}]);self.assertEqual(len(r.valid_audits()),0);self.assertEqual(len(r.metadata('audits')),1)
