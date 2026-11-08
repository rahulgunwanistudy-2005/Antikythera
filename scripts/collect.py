"""Acquire a bounded, resumable review queue. Offline by default.

No proposal enters the reviewed analysis population automatically.
"""
import argparse,hashlib,json,re,time
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from extract.baseline import extract_culpeper
from extract.claims import validate_claim
from extract.adapters import manuscript_chapters,modern_oa_table
from extract.historical import propose_manuscript
from extract.jats import medicinal_table
from identity.resolver import Resolver
from ledger.cache import CacheMiss
from ledger.europepmc import EuropePMC,normalise
from ledger.queries import plan,VERSION
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_SPECIES=('Colchicum autumnale','Galanthus nivalis','Galega officinalis','Papaver somniferum','Taxus brevifolia','Catharanthus roseus')

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n');temp.replace(path)

def validate_proposal(row,text):
    if row.get('reviewed') or row.get('analysis_eligible'):raise ValueError('Automated proposals cannot mark review complete')
    # Validate source material independently of the unresolved historical date.
    copy={**row,'year':row.get('year') if type(row.get('year')) is int else row.get('edition_year',0)}
    if copy['year'] is None:copy['year']=0
    return validate_claim(copy,text)

def collect(root=ROOT,fetch=False,species=DEFAULT_SPECIES,categories=('joint','metabolic','neuro'),max_records=6,effort_years=(1900,1950,1980,2000,2010),source_ids=None):
    root=Path(root);derived=root/'data/derived';raw=root/'data/raw/cache';source_rows=json.loads((root/'data/raw/sources.json').read_text())['sources']
    source_status=[];claims=[];chapter_count=0
    selected=set(source_ids or ['culpeper-gutenberg-49513','dioscorides-berendes-1902','paul-adams-1844-1847','balkan-open-access'])
    for source in source_rows:
        source_id=source['id'];path=root/source.get('local_text_path','data/raw/cache/texts/'+source_id+'.txt')
        status={'source_id':source_id,'layer':source.get('layer'),'catalog_url':source.get('catalog_url'),'licence_status':source.get('licence_status'),'edition_warning':source.get('edition_warning'),'status':'not_selected','chapters':0,'proposed_claims':0}
        if source_id in selected:
            if not path.is_file() and fetch and source.get('download_allowed'):
                from data.raw.download import download
                download(source_id,path.parent,root/'data/raw/sources.json')
            if not path.is_file():status.update(status='blocked',reason='Local source missing or licence/edition gate not cleared')
            elif source_id=='culpeper-gutenberg-49513':
                text=path.read_text();digest=hashlib.sha256(path.read_bytes()).hexdigest();chapters,rows=extract_culpeper(text,source,path.relative_to(root),digest)
                for row in rows:validate_proposal(row,text)
                claims.extend(rows);chapter_count+=len(chapters);status.update(status='extracted_proposals',chapters=len(chapters),proposed_claims=len(rows),source_sha256=digest,edition_year=source.get('edition_year'))
            else:
                try:
                    if source.get('adapter') in ('berendes_german_ocr_v1','paul_book7_ocr_v1'):
                        if not source.get('local_import_allowed'):raise ValueError('Manuscript licence gate closed')
                        text=path.read_text();digest=hashlib.sha256(path.read_bytes()).hexdigest()
                        chapters,rows=propose_manuscript(text,source,path.relative_to(root),digest)
                        for row in rows:validate_proposal(row,text)
                        claims.extend(rows);chapter_count+=len(chapters);status.update(status='extracted_proposals',chapters=len(chapters),proposed_claims=len(rows),source_sha256=digest,edition_year=source.get('edition_year'))
                        source_status.append(status);continue
                    if source.get('adapter')=='licensed_jats_medicinal_table_v1':
                        if not source.get('local_import_allowed'):raise ValueError('JATS licence gate closed')
                        entries,rows=medicinal_table(path,source,root)
                        for row in rows:validate_proposal(row,(root/row['source_text_path']).read_text())
                        claims.extend(rows);status.update(status='extracted_proposals',chapters=0,table_rows=len(entries),proposed_claims=len(rows),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),edition_year=2014)
                        source_status.append(status);continue
                    if source.get('adapter')=='licensed_oa_csv_v1':
                        if not source.get('local_import_allowed'):raise ValueError('OA table licence gate closed')
                        metadata=source.get('table_metadata',{})
                        rows=modern_oa_table(path,metadata)
                        for row in rows:row.update(source_text_path=str(path.relative_to(root)),source_id=source_id,licence_reviewed=False,identity_id=None,method='licensed_table_import',review_blockers=['source_interpretation','identity','licence_jurisdiction'])
                        claims.extend(rows);status.update(status='extracted_proposals',proposed_claims=len(rows));source_status.append(status);continue
                    imported=manuscript_chapters(source,root);chapter_count+=len(imported['chapters']);status.update(status='chaptered_model_or_review_pending',chapters=len(imported['chapters']))
                except ValueError as error:status.update(status='blocked',reason=str(error))
        elif source.get('layer') in ('dioscorides','byzantine','balkan'):status.update(status='blocked',reason=source.get('blocked_reason','Licence, edition or licensed source selection pending'))
        source_status.append(status)
    resolver=Resolver(raw/'taxonomy',offline=not fetch);taxa=[];evidence=[];effort=[];searches=[];errors=[];client=EuropePMC(raw/'europepmc',offline=not fetch)
    record_dir=raw/'evidence_records';record_dir.mkdir(parents=True,exist_ok=True)
    for name in species:
        try:
            taxon=resolver.resolve(name)
            for key in ('record_path','metadata_path'):taxon[key]=str(Path(taxon[key]).relative_to(root))
            taxa.append(taxon)
        except (CacheMiss,RuntimeError,ValueError) as error:
            taxa.append({'id':'taxon-pending-'+re.sub(r'[^a-z]+','-',name.lower()),'query_name':name,'species_id':name,'family':None,'backbone_version':None,'source_url':None,'candidates':[],'reviewed':False,'status':'cache_missing' if isinstance(error,CacheMiss) else 'fetch_failed','reason':str(error)})
        for search in plan(name):
            if search['category'] not in categories:continue
            query=search['europepmc_query']
            state={**search,'provider':'EuropePMC','status':'pending','retrieved':0,'complete':False}
            try:
                found=client.search(query,max_records)
                state.update(status='retrieved',retrieved=found['returned'],total_hits=found['total_hits'],complete=found['complete'],truncated=found['truncated'])
                for raw_row,saved,page in found['records']:
                    record=normalise(raw_row)
                    if not record['pmid']:continue
                    record_path=record_dir/(str(record['pmid'])+'.json')
                    # Immutable evidence file allows reviewer proof of exact version.
                    record_data={**record,'retrieved_at':saved['fetched_at'],'provider':'EuropePMC','raw_page_sha256':hashlib.sha256(page.read_bytes()).hexdigest()}
                    if not record_path.exists():dump(record_path,record_data)
                    record_data=json.loads(record_path.read_text())
                    identifier='evidence-'+hashlib.sha256((name+'|'+search['category']+'|'+str(record['pmid'])).encode()).hexdigest()[:18]
                    evidence.append({'id':identifier,'pmid':str(record['pmid']),'species_id':name,'category':search['category'],'year':record['year'],'first_publication_date':record['first_publication_date'],'date_basis':record['date_basis'],'title':record['title'],'source_url':record['source_url'],'record_path':str(record_path.relative_to(root)),'record_sha256':hashlib.sha256(record_path.read_bytes()).hexdigest(),'verdict':None,'evidence_tier':None,'preparation_scope':'unclear','rationale':'Retrieved query match. Relevance and experimental verdict require grading.','reviewed':False,'study_type':'unclassified','publication_types':record['publication_types'],'status':'ungraded','query':query,'query_version':VERSION,'has_abstract':bool(record_data['abstract']),'abstract_redistribution':'not_in_public_proposal','analysis_eligible':False})
            except (CacheMiss,RuntimeError,ValueError,KeyError) as error:state.update(status='cache_missing' if isinstance(error,CacheMiss) else 'fetch_failed',reason=str(error))
            searches.append(state)
        # Annual counts, never today's volume masquerading as earlier effort.
        for year in effort_years:
            query='TITLE_ABS:"'+name+'" AND SRC:MED AND FIRST_PDATE:['+str(year)+'-01-01 TO '+str(year)+'-12-31]'
            try:
                count,saved,path=client.count(query)
                effort.append({'id':'effort-'+hashlib.sha256((name+str(year)).encode()).hexdigest()[:18],'species_id':name,'year':year,'count':count,'query':query,'synonym_version':'accepted-name-only-v1','coverage_reviewed':False,'provider':'EuropePMC','retrieved_at':saved['fetched_at'],'source_url':saved['url'],'record_path':str(path.relative_to(root)),'record_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':'proposed','note':'One annual count, not complete pre-freeze history. Accepted-name-only coverage requires synonym audit.'})
            except (CacheMiss,RuntimeError,ValueError,KeyError) as error:errors.append({'task':'annual_effort','species_id':name,'year':year,'status':'cache_missing' if isinstance(error,CacheMiss) else 'fetch_failed','reason':str(error)})
    collection={'schema_version':1,'status':'proposals_pending_human_review','run':{'date':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'mode':'fetch' if fetch else 'offline','max_records_per_query':max_records,'selected_species':list(species),'categories':list(categories),'effort_years':list(effort_years)},'counts':{'sources_with_text':sum(s['status'] in ('extracted_proposals','chaptered_model_or_review_pending') for s in source_status),'chapters':chapter_count,'table_rows':sum(s.get('table_rows',0) for s in source_status),'proposed_claims':len(claims),'historical_names':len({r['plant_name_as_written'] for r in claims}),'retrieved_evidence_rows':len(evidence),'unique_pmids':len({r['pmid'] for r in evidence}),'evidence_rows_with_abstract':sum(r['has_abstract'] for r in evidence),'taxonomy_candidates':sum(bool(t.get('candidates')) for t in taxa),'annual_effort_observations':len(effort),'human_reviewed_claims':0,'human_reviewed_grades':0},'source_status':source_status,'searches':searches,'errors':errors,'analysis_eligible':False,'limitations':['Baseline extraction has no measured precision or recall.','Modern name queries are seeded demonstrations, not resolved identities of Culpeper chapters.','Capped evidence samples cannot establish first-tested, first-confirmed or never-tested status.','Annual effort snapshots do not constitute complete research effort histories.','No automated proposal is a human audit or calibrated probability.','Historical dates and edition attribution require review.','German OCR uses a bilingual lexicon with unreviewed commentary boundaries.','Paul proposals exclude text after explicit Commentary markers but botanical scope remains unreviewed.','Balkan table spans reference a whitelisted normalised projection linked to the original licensed JATS hash.','Abstract text remains only in ignored local cache.']}
    for filename,rows in [('claims_proposed.json',claims),('evidence_proposed.json',evidence),('taxa_proposed.json',taxa),('effort_proposed.json',effort),('collection.json',collection)]:dump(derived/filename,rows)
    return collection

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--offline',action='store_true');parser.add_argument('--species',action='append');parser.add_argument('--category',action='append');parser.add_argument('--source',action='append');parser.add_argument('--max-records',type=int,default=6);parser.add_argument('--effort-year',action='append',type=int);args=parser.parse_args()
    if args.fetch and args.offline:parser.error('Choose --fetch or --offline')
    result=collect(fetch=args.fetch,species=args.species or DEFAULT_SPECIES,categories=args.category or ('joint','metabolic','neuro'),max_records=args.max_records,effort_years=args.effort_year if args.effort_year is not None else (1900,1950,1980,2000,2010),source_ids=args.source)
    print(json.dumps(result['counts'],indent=2))
if __name__=='__main__':main()
