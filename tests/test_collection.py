import csv,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from extract.adapters import modern_oa_table,manuscript_chapters
from extract.baseline import extract_culpeper
from extract.provider import StructuredProvider
from harmonise.baseline import Harmoniser
from ledger.cache import CacheMiss,JsonCache
from ledger.europepmc import EuropePMC,normalise
from ledger.queries import plan
from scripts.collect import collect,validate_proposal

TEXT='''    HERB.

_Descript._] Green leaves.

_Government and virtues._] It helps the dropsy and cures the cough.

    OTHER HERB.

_Descript._] Other leaves.

_Government and virtues._] It cures wounds.
'''
SOURCE={'id':'culpeper-gutenberg-49513','catalog_url':'https://www.gutenberg.org/ebooks/49513','layer':'renaissance','edition_year':1850}

class CollectionTests(unittest.TestCase):
    def test_baseline_preserves_source_and_unresolved_dates(self):
        chapters,rows=extract_culpeper(TEXT,SOURCE,Path('data/raw/cache/text.txt'),hashlib.sha256(TEXT.encode()).hexdigest())
        self.assertEqual(len(chapters),2);self.assertGreaterEqual(len(rows),3)
        for row in rows:
            validate_proposal(row,TEXT)
            self.assertIsNone(row['year']);self.assertFalse(row['reviewed']);self.assertFalse(row['analysis_eligible'])
            self.assertEqual(TEXT[row['span_start']:row['span_end']],row['source_span'])
        with self.assertRaises(ValueError):validate_proposal({**rows[0],'plant_context_span':'fake'},TEXT)
    def test_harmonisation_scores_are_not_probabilities(self):
        result=Harmoniser().propose('dropsy urinary stones')
        self.assertEqual(result['candidates'][0]['category'],'urinary')
        self.assertFalse(result['calibrated']);self.assertTrue(result['requires_adjudication'])
    def test_offline_never_opens_socket(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch('ledger.cache.urlopen',side_effect=AssertionError('network')):
                with self.assertRaises(CacheMiss):JsonCache(temp,offline=True).get('https://example.com')
    def test_oa_table_omits_community_fields_and_checks_license(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'table.csv';p.write_text('plant_name,ailment,village,informant\nPlant,dropsy,private,private\n')
            meta=dict(article_url='https://example.com/article',licence_url='https://creativecommons.org/licenses/by/4.0/',licence='CC-BY-4.0',publication_year=2010,table_id='t1',attribution='Author',version='v1')
            rows=modern_oa_table(p,meta)
            self.assertNotIn('village',rows[0]);self.assertNotIn('informant',rows[0]);self.assertFalse(rows[0]['reviewed'])
            with self.assertRaises(ValueError):modern_oa_table(p,{**meta,'licence':'unknown'})
    def test_uncleared_manuscript_gate(self):
        with self.assertRaises(ValueError):manuscript_chapters({'id':'x','local_import_allowed':False},Path('.'))
    def test_evidence_normalisation_keeps_compound_ungraded(self):
        result=normalise({'source':'MED','id':'123','title':'Study','firstPublicationDate':'1988-01-02','abstractText':'A result'})
        self.assertEqual(result['pmid'],'123');self.assertEqual(result['year'],1988);self.assertFalse(result['reviewed']);self.assertNotIn('verdict',result)
    def test_truncation_is_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            client=EuropePMC(temp)
            client.cache.get=lambda url:({'hitCount':100,'resultList':{'result':[{'source':'MED','id':'1'}]},'nextCursorMark':'next'},{},Path(temp))
            result=client.search('x',max_records=1)
            self.assertTrue(result['truncated']);self.assertFalse(result['complete']);self.assertEqual(result['total_hits'],100)
    def test_query_planner_includes_unclaimed_categories(self):
        queries=plan('Plant species',['Plant synonym'])
        self.assertEqual(len(queries),12)
        self.assertTrue(all('Plant synonym' in q['pubmed_query'] for q in queries))
    def test_provider_requires_https_without_credential_url(self):
        with self.assertRaises(ValueError):StructuredProvider('http://remote.example.com')
        with self.assertRaises(ValueError):StructuredProvider('https://secret@example.com')
        self.assertEqual(StructuredProvider('http://localhost:8080').endpoint,'http://localhost:8080')
    def test_offline_collection_is_reproducible_and_omits_abstracts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data/raw/cache/texts').mkdir(parents=True)
            (root/'data/raw/sources.json').write_text(json.dumps({'sources':[SOURCE]}))
            (root/'data/raw/cache/texts/culpeper-gutenberg-49513.txt').write_text(TEXT)
            first=collect(root,False,species=(),effort_years=())
            before=(root/'data/derived/claims_proposed.json').read_text()
            second=collect(root,False,species=(),effort_years=())
            self.assertEqual(first['counts'],second['counts']);self.assertEqual(before,(root/'data/derived/claims_proposed.json').read_text())
            self.assertEqual(json.loads((root/'data/derived/evidence_proposed.json').read_text()),[])
if __name__=='__main__':unittest.main()
