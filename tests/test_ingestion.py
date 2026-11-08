"""Synthetic tests for the boundary between narrative data and empirical input."""
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from scripts.build_dataset import build

class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.reviewed=self.root/'reviewed';self.reviewed.mkdir()
        for name in ('claims','identities','taxa','grades','effort'):self.put(name,[])
        self.put('coverage',{'observation_end':2026,'search_complete':False,'effort_coverage_complete':False})
    def put(self,name,value):
        (self.reviewed/(name+'.json')).write_text(json.dumps(value))
    def fixture(self):
        text='Imaginary plant treats dropsy.';source=self.root/'source.txt';source.write_text(text)
        self.put('taxa',[{'species_id':'Synthetic species','family':'Synthetic family','reviewed':True,'backbone_version':'fixture','source_url':'https://example.com/taxon'}])
        self.put('identities',[{'id':'prior','reviewed':True,'reviewer':'fixture reviewer','available_year':1800,'source_url':'https://example.com/prior','candidates':[{'species_id':'Synthetic species','probability':1}]}])
        claim={'id':'claim','source_id':'fixture','plant_name_as_written':'Imaginary plant','ailment_as_written':'dropsy','part':None,'preparation':None,'span_start':0,'span_end':len(text),'source_span':text,'category':'urinary','year':1653,'era':'renaissance','reviewed':True,'reviewer':'fixture reviewer','historical_date_reviewed':True,'licence_reviewed':True,'source_text_path':'source.txt','source_sha256':hashlib.sha256(text.encode()).hexdigest(),'source_url':'https://example.com/source','identity_id':'prior'}
        self.put('claims',[claim]);return claim
    def test_empty_is_valid_but_not_empirical(self):
        d=build(self.reviewed,self.root);self.assertEqual(d['claims'],[]);self.assertFalse(d['coverage']['search_complete'])
    def test_curated_demo_narrative_cannot_enter_analysis(self):
        self.put('claims',[{'category':'joint','year':500,'text':'Narrative','status':'curated_unreviewed'}])
        with self.assertRaisesRegex(ValueError,'review'):build(self.reviewed,self.root)
    def test_changed_source_rejected(self):
        self.fixture();(self.root/'source.txt').write_text('Altered source')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):build(self.reviewed,self.root)
    def test_verified_offsets_and_prior_are_preserved(self):
        self.fixture();d=build(self.reviewed,self.root)
        self.assertEqual(d['claims'][0]['identity_available_year'],1800)
        self.assertEqual(d['claim_provenance'][0]['span_start'],0)
    def test_source_path_escape_rejected(self):
        c=self.fixture();c['source_text_path']='../outside.txt';self.put('claims',[c])
        with self.assertRaisesRegex(ValueError,'within'):build(self.reviewed,self.root)
    def test_compound_grade_never_promoted(self):
        self.fixture();raw=b'{"pmid":"123","abstract":"Synthetic evidence"}';(self.root/'record.json').write_bytes(raw)
        self.put('grades',[{'pmid':'123','species_id':'Synthetic species','category':'urinary','year':1905,'verdict':'supports','evidence_tier':'clinical','rationale':'Synthetic fixture','reviewed':True,'reviewer':'fixture reviewer','study_type':'original','record_path':'record.json','record_sha256':hashlib.sha256(raw).hexdigest(),'preparation_scope':'compound_only'}])
        self.assertEqual(build(self.reviewed,self.root)['ledger'],[])
    def test_unreviewed_dates_cannot_enter(self):
        c=self.fixture();c['historical_date_reviewed']=False;self.put('claims',[c])
        with self.assertRaisesRegex(ValueError,'date review'):build(self.reviewed,self.root)

if __name__=='__main__':unittest.main()
