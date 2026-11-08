import unittest
from audit.scoring import score,stratified_sample

class AuditScoringTests(unittest.TestCase):
    def row(self,task='harmonisation',id_='one',gold=None,prediction=None):return {'task':task,'item_id':id_,'reviewer':'Synthetic reviewer','independent':True,'attested':True,'gold':gold or {'category':'urinary'},'prediction':prediction or {'category':'urinary'}}
    def test_empty_templates_not_counted(self):
        r=score([{'task':'extraction','gold':None,'prediction':{}}]);self.assertEqual(r['completed']['extraction'],0);self.assertFalse(r['targets_met'])
    def test_confusion_uses_independent_gold(self):
        rows=[self.row(),self.row(id_='two',prediction={'category':'gi'})];s=score(rows)['tasks']['harmonisation']
        self.assertEqual(s['accuracy']['estimate'],.5);self.assertEqual(s['classes']['urinary']['recall']['estimate'],.5)
    def test_extraction_recall_requires_complete_passage(self):
        s=score([self.row('extraction',gold={'correct':True},prediction={'category':'urinary'})])['tasks']['extraction'];self.assertEqual(s['precision']['estimate'],1);self.assertIsNone(s['recall']['estimate'])
    def test_duplicate_audit_item_rejected(self):
        with self.assertRaises(ValueError):score([self.row(),self.row()])
    def test_stratified_sampling_seeded_and_bounded(self):
        rows=[{'id':str(i),'category':str(i%3),'era':'fixture'} for i in range(50)]
        a=stratified_sample(rows,12);self.assertEqual(a,stratified_sample(rows,12));self.assertEqual(len(a),12);self.assertEqual(len({r['category'] for r in a}),3)
    def test_identity_ece_is_measured_only_from_labels(self):
        row=self.row('identity',gold={'species_id':'SyntheticA'},prediction={'species_id':'SyntheticA','probability':.8})
        self.assertAlmostEqual(score([row])['tasks']['identity']['ece'],.2)
