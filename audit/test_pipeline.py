import unittest
from extract.claims import chunks,validate_claim
from identity.calibration import validate_candidates,reliability
from audit.metrics import wilson
from ledger.grades import build_ledger
from ledger.pubmed import PubMed
from tempfile import TemporaryDirectory

class PipelineTests(unittest.TestCase):
    def test_source_offsets_and_hallucinations(self):
        source='Plant treats dropsy.'
        row=dict(id='c',source_id='s',plant_name_as_written='Plant',ailment_as_written='dropsy',part=None,preparation=None,span_start=0,span_end=len(source),source_span=source,category='urinary',year=60,era='dioscorides')
        self.assertEqual(validate_claim(row,source),row)
        with self.assertRaises(ValueError):validate_claim({**row,'source_span':'invented'},source)
        with self.assertRaises(ValueError):validate_claim({**row,'plant_name_as_written':'Moly'},source)
    def test_chunk_offsets(self):
        text='# Chapter\nabc\n# Next\nxyz'
        rows=list(chunks(text,8))
        self.assertEqual(''.join(r['text'] for r in rows),text)
        for r in rows:self.assertEqual(r['text'],text[r['start']:r['end']])
    def test_unreviewed_identity_blocked(self):
        with self.assertRaises(ValueError):validate_candidates([{'species_id':'s','probability':None}])
        with self.assertRaises(ValueError):validate_candidates([{'species_id':'s','probability':.8}])
    def test_no_empty_audit_precision(self):
        self.assertIsNone(wilson(0,0)['estimate'])
        self.assertAlmostEqual(reliability([1,.5],[1,0])['ece'],.25)
    def test_compound_story_not_botanical_confirmation(self):
        row=dict(pmid='123',species_id='s',category='neuro',year=1957,verdict='supports',evidence_tier='clinical',rationale='test',reviewed=True,preparation_scope='compound_only')
        self.assertEqual(build_ledger([row]),[])
        self.assertEqual(build_ledger([{**row,'preparation_scope':'botanical','reviewed':False}]),[])
        self.assertEqual(build_ledger([{**row,'preparation_scope':'botanical','evidence_tier':'in_vitro'}])[0]['confirmed_year'],None)
        self.assertEqual(build_ledger([{**row,'preparation_scope':'botanical'}])[0]['confirmed_year'],1957)
    def test_pubmed_fails_on_truncation(self):
        with TemporaryDirectory() as cache:
            client=PubMed(cache,'audit@example.com')
            client.request=lambda *a,**k:'{"esearchresult":{"count":"10001"}}'
            with self.assertRaises(ValueError):client.search('x')
if __name__=='__main__':unittest.main()
