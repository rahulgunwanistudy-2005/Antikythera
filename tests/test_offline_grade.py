import hashlib,unittest
from ledger.offline_grade import suggest

class OfflineGradeTests(unittest.TestCase):
    def grade(self,text,types=None,category='metabolic'):
        return suggest({'abstract':text,'publication_types':types or ['Journal Article'],'title':''},'Galega officinalis',category)
    def test_word_hits_abstain(self):
        r=self.grade('Galega officinalis is traditionally associated with diabetes. Its extract may be useful.')
        self.assertIsNone(r['verdict']);self.assertTrue(r['abstain']);self.assertFalse(r['reviewed'])
    def test_compound_only_never_botanical(self):
        r=self.grade('Purified compounds from Galega officinalis were administered to rats with diabetes. The compounds significantly reduced blood glucose compared to controls.')
        self.assertEqual(r['preparation_scope'],'compound_only');self.assertIsNone(r['verdict'])
    def test_review_not_original(self):
        r=self.grade('Galega officinalis extract was administered to rats compared with controls. The extract significantly reduced blood glucose.',types=['Review'])
        self.assertEqual(r['study_type'],'review');self.assertIsNone(r['verdict'])
    def test_narrow_positive_is_only_a_proposal(self):
        r=self.grade('Galega officinalis extract was administered to diabetic rats compared with controls. The extract significantly reduced blood glucose.')
        self.assertEqual(r['verdict'],'supports');self.assertFalse(r['reviewed']);self.assertEqual(r['evidence_tier'],'in_vivo')
    def test_negative_requires_explicit_result(self):
        r=self.grade('Galega officinalis extract was administered to diabetic rats compared with controls. The extract did not significantly reduce blood glucose.')
        self.assertEqual(r['verdict'],'refutes');self.assertFalse(r['reviewed'])
    def test_qualified_positive_abstains(self):
        r=self.grade('Galega officinalis extract was administered to diabetic rats compared with controls. The extract may have significantly reduced blood glucose.')
        self.assertIsNone(r['verdict'])
    def test_conflicting_results_abstain(self):
        r=self.grade('Galega officinalis extract was administered to diabetic rats compared with controls. The extract significantly reduced blood glucose. The extract did not significantly reduce blood glucose.')
        self.assertIsNone(r['verdict']);self.assertTrue(r['abstain'])
    def test_missing_species_cannot_support(self):
        r=self.grade('An unrelated plant extract was administered to diabetic rats compared with controls. The extract significantly reduced blood glucose.')
        self.assertIsNone(r['verdict'])
    def test_offsets_and_hash_reference_exact_raw_string(self):
        text='The <i>Galega officinalis</i> extract was given to rats with diabetes.'
        r=self.grade(text)
        self.assertEqual(r['abstract_sha256'],hashlib.sha256(text.encode()).hexdigest())
        for span in r['evidence_spans']:
            self.assertEqual(set(span),{'label','start','end'});self.assertGreater(span['end'],span['start']);self.assertLessEqual(span['end'],len(text))
        species=next(s for s in r['evidence_spans'] if s['label']=='target_species')
        self.assertEqual(text[species['start']:species['end']],'Galega officinalis')
    def test_scope_and_tier_mixture_abstains(self):
        r=self.grade('Galega officinalis extract was administered to diabetic rats compared with controls. Purified compounds were tested in cell cultures. The extract significantly reduced blood glucose.')
        self.assertEqual(r['preparation_scope'],'unclear');self.assertIsNone(r['evidence_tier']);self.assertIsNone(r['verdict'])
    def test_empty_abstract_abstains(self):
        r=self.grade('');self.assertTrue(r['abstain']);self.assertIsNone(r['verdict']);self.assertIsNone(r['evidence_tier'])
if __name__=='__main__':unittest.main()
