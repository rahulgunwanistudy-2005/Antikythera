"""Validate review fields against frozen source evidence; never invent completion."""
import hashlib
import re
from pathlib import Path
from extract.claims import CATEGORIES,validate_claim
from ledger.grades import validate_grade
from identity.calibration import validate_candidates

COMMON={'category','rationale'}
ALLOWED={
'claim':COMMON|{'year','historical_date_reviewed','historical_date_note','licence_reviewed','identity_id','part','preparation','plant_name_as_written','ailment_as_written'},
'evidence':COMMON|{'year','verdict','evidence_tier','preparation_scope','study_type'},
'identity':{'candidates','available_year','source_url','calibration_status','calibration_audit_id','calibration_note'},
'taxon':{'species_id','family','backbone_version','source_url','regions','hazard_trail'},
'effort':{'coverage_reviewed','query','synonym_version','count','year'},
'harmonisation':{'category','rationale'},
}

def checked_path(root,path):
    root=Path(root).resolve();path=(root/path).resolve()
    if not path.is_relative_to(root):raise ValueError('Record path must remain within the project')
    return path

def validate_review(kind,record,fields,root,decision='accept'):
    if kind not in ALLOWED:raise ValueError('Unknown review kind')
    unknown=set(fields)-ALLOWED[kind]
    if unknown:raise ValueError('Unsupported review fields: '+', '.join(sorted(unknown)))
    if decision!='accept':return fields
    merged={**record,**fields,'reviewed':True}
    if 'category' in merged and merged['category'] not in CATEGORIES:raise ValueError('Choose a prespecified indication category')
    if kind=='claim':
        raw=checked_path(root,merged['source_text_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=merged['source_sha256']:raise ValueError('Source file changed; re-collect before review')
        # A span may be reviewed while historical dating remains unresolved.
        claim={**merged,'year':merged.get('year') if type(merged.get('year')) is int else 0}
        validate_claim(claim,raw.decode('utf-8'))
        if merged.get('historical_date_reviewed') is True:
            if type(merged.get('year')) is not int or not merged.get('historical_date_note','').strip():raise ValueError('Historical date review needs a year and a supporting note')
    elif kind=='evidence':
        validate_grade(merged)
        if merged.get('study_type') not in ('original','review','unclassified','other'):raise ValueError('Choose original study, review, or unclassified')
        raw=checked_path(root,merged['record_path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=merged['record_sha256']:raise ValueError('Evidence record changed; re-collect before review')
    elif kind=='identity':
        validate_candidates(merged.get('candidates',[]))
        if type(merged.get('available_year')) is not int or not merged.get('source_url'):raise ValueError('Identity needs availability year and source')
    elif kind=='taxon':
        if not all(merged.get(k) for k in ('species_id','family','backbone_version','source_url')):raise ValueError('Taxon needs accepted name, family and versioned source')
        if not isinstance(merged.get('regions',[]),list) or not isinstance(merged.get('hazard_trail',[]),list):raise ValueError('Regions and hazard trail must be arrays')
    elif kind=='effort':
        if type(merged.get('count')) is not int or merged['count']<0 or type(merged.get('year')) is not int:raise ValueError('Effort needs nonnegative annual count and year')
        if not merged.get('coverage_reviewed') or not merged.get('query') or not merged.get('synonym_version'):raise ValueError('Effort query and synonym coverage review required')
    return fields
