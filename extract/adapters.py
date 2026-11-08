"""Licence-gated imports for all prespecified layers.

Imports create proposals. User-supplied metadata cannot mark human review.
"""
import csv,hashlib,json
from pathlib import Path
from extract.chapters import generic_chapters

def registered_text(source,root):
    if not source.get('download_allowed') and not source.get('local_import_allowed'):
        raise ValueError('Source licence/version gate closed: '+source['id'])
    path=(Path(root)/source.get('local_text_path','')).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_file():raise ValueError('Registered local text missing or outside project')
    raw=path.read_bytes();text=raw.decode('utf-8')
    expected=source.get('source_sha256')
    if expected and hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Registered source hash mismatch')
    return path,text,hashlib.sha256(raw).hexdigest()

def manuscript_chapters(source,root):
    path,text,digest=registered_text(source,root)
    if source['layer'] not in ('dioscorides','byzantine','renaissance'):raise ValueError('Unknown manuscript layer')
    if not source.get('edition_id') or not source.get('commentary_policy'):raise ValueError('Edition ID and commentary policy required')
    chapters=generic_chapters(text,source.get('heading_pattern',r'(?m)^#{1,4} (.+)$'))
    return {'source_id':source['id'],'path':str(path),'text':text,'sha256':digest,'chapters':chapters,'reviewed':False}

def modern_oa_table(path,metadata):
    required=('article_url','licence_url','licence','publication_year','table_id','attribution','version')
    if any(not metadata.get(k) for k in required):raise ValueError('OA table requires article, attribution, licence and version')
    if metadata['licence'] not in ('CC-BY-4.0','CC-BY-3.0','CC0-1.0'):raise ValueError('Uncleared OA table licence')
    if type(metadata['publication_year']) is not int:raise ValueError('Publication year must be integer')
    raw=Path(path).read_bytes();digest=hashlib.sha256(raw).hexdigest();rows=[]
    for i,row in enumerate(csv.DictReader(raw.decode('utf-8').splitlines()),2):
        if not all(row.get(k) for k in ('plant_name','ailment')):raise ValueError('CSV requires plant_name and ailment at line '+str(i))
        # Whitelist excludes locality, informants and community identifiers.
        rows.append({'id':'oa-'+digest[:12]+'-'+str(i),'source_id':metadata['table_id'],'source_url':metadata['article_url'],'plant_name_as_written':row['plant_name'],'ailment_as_written':row['ailment'],'part':row.get('part') or None,'preparation':row.get('preparation') or None,'year':metadata['publication_year'],'era':'balkan','source_table_row':i,'source_sha256':digest,'licence':metadata['licence'],'licence_url':metadata['licence_url'],'attribution':metadata['attribution'],'reviewed':False,'historical_date_reviewed':False,'status':'proposed','analysis_eligible':False})
    return rows
