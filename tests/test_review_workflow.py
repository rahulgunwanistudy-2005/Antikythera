"""All records below are synthetic, isolated from the actual research repository."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from storage.repository import Repository
from storage.review import validate_review
from scripts.promote import promote
from scripts.build_dataset import build

class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.repo=Repository(self.root/'local.duckdb')
        (self.root/'data/reviewed').mkdir(parents=True);(self.root/'data/derived').mkdir(parents=True)
        for n in ('claims','identities','taxa','grades','effort'):(self.root/f'data/reviewed/{n}.json').write_text('[]')
        (self.root/'data/reviewed/coverage.json').write_text('{"observation_end":2026,"search_complete":false}')
        text='Synthetic plant treats dropsy.';(self.root/'source.txt').write_text(text)
        self.claim={'id':'claim','source_id':'synthetic','source_url':'https://example.org/source','source_text_path':'source.txt','source_sha256':hashlib.sha256(text.encode()).hexdigest(),'plant_name_as_written':'Synthetic plant','ailment_as_written':'dropsy','part':None,'preparation':None,'span_start':0,'span_end':len(text),'source_span':text,'category':'urinary','year':None,'era':'renaissance','identity_id':'prior','historical_date_reviewed':False,'licence_reviewed':False}
        self.repo.sync('claim',[self.claim])
    def accept(self,kind,id_,fields):
        row=self.repo.get(kind,id_);validate_review(kind,row,fields,self.root)
        return self.repo.review(kind,id_,'Synthetic reviewer','accept','Synthetic test decision',row['revision'],fields,True)
    def taxon_prior(self):
        self.repo.sync('taxon',[{'id':'taxon','species_id':'Synthetic species','family':'Synthetic family','backbone_version':'fixture-v1','source_url':'https://example.org/taxa'}]);self.accept('taxon','taxon',{})
        self.repo.sync('identity',[{'id':'prior','candidates':[{'species_id':'Synthetic species','probability':1}],'available_year':1800,'source_url':'https://example.org/identity'}]);self.accept('identity','prior',{})
    def test_partial_span_review_cannot_become_analysis(self):
        self.accept('claim','claim',{});status=promote(self.root,self.repo)
        self.assertEqual(build(self.root/'data/reviewed',self.root)['claims'],[]);self.assertTrue(status['blocked_reviews'])
    def test_complete_review_chain_preserves_temporal_and_span_provenance(self):
        self.taxon_prior();self.accept('claim','claim',{'year':1653,'historical_date_reviewed':True,'historical_date_note':'Synthetic dated original edition','licence_reviewed':True})
        promote(self.root,self.repo);data=build(self.root/'data/reviewed',self.root)
        self.assertEqual(data['claims'][0]['year'],1653);self.assertEqual(data['claims'][0]['identity_available_year'],1800);self.assertEqual(data['claim_provenance'][0]['span_end'],len(self.claim['source_span']))
    def test_revoked_prior_removes_dependent_claim_without_leaving_stale_export(self):
        self.taxon_prior();self.accept('claim','claim',{'year':1653,'historical_date_reviewed':True,'historical_date_note':'Synthetic date','licence_reviewed':True});promote(self.root,self.repo)
        row=self.repo.get('identity','prior');self.repo.review('identity','prior','Synthetic reviewer','reject','Synthetic revocation',row['revision'],{},True)
        promote(self.root,self.repo);data=build(self.root/'data/reviewed',self.root)
        self.assertEqual(data['identities'] if 'identities' in data else data['claims'],[]);self.assertEqual(data['claims'],[])
