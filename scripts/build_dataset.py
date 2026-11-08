"""Fail closed when turning reviewed provenance records into analysis inputs."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from extract.claims import validate_claim
from identity.calibration import validate_candidates
from ledger.grades import build_ledger, validate_grade
from timemachine.engine import validate_dataset

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def build(reviewed, root=ROOT):
    coverage = read_json(reviewed / 'coverage.json')
    claims, identities, taxa, grades, effort = [read_json(reviewed / (n+'.json')) for n in ('claims','identities','taxa','grades','effort')]
    for rows in (claims, identities, taxa, grades, effort):
        if not isinstance(rows, list):
            raise ValueError('Reviewed record files must be JSON arrays')
    priors = {}
    for prior in identities:
        if not prior.get('reviewed') or not prior.get('reviewer'):
            raise ValueError('Every ingested identity prior needs a reviewer')
        validate_candidates(prior['candidates'])
        if type(prior.get('available_year')) is not int:
            raise ValueError('Identity prior availability year required')
        if not prior.get('source_url') or not prior.get('id') or prior['id'] in priors:
            raise ValueError('Unique prior id and provenance URL required')
        priors[prior['id']] = prior
    accepted_taxa = []
    for taxon in taxa:
        if not taxon.get('reviewed') or not taxon.get('backbone_version') or not taxon.get('source_url'):
            raise ValueError('Taxa require reviewed backbone version and provenance')
        accepted_taxa.append({'species': taxon['species_id'], 'family': taxon['family'], 'regions':taxon.get('regions',[]), 'hazard_trail':taxon.get('hazard_trail',[]), 'backbone_version':taxon['backbone_version'], 'source_url':taxon['source_url']})
    analysis_claims = []
    sources = []
    for claim in claims:
        if not claim.get('reviewed') or not claim.get('reviewer') or not claim.get('historical_date_reviewed'):
            raise ValueError('Claim needs human span and historical date review')
        path = (root / claim['source_text_path']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Source path must stay within the project')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != claim.get('source_sha256'):
            raise ValueError('Source hash mismatch')
        if not claim.get('licence_reviewed') or not claim.get('source_url'):
            raise ValueError('Claim requires licence review and a provenance URL')
        validate_claim(claim, raw.decode('utf-8'))
        if claim['era'] not in ('dioscorides','byzantine','renaissance','balkan'):
            raise ValueError('Analysis claim must belong to a prespecified corpus layer')
        prior = priors[claim['identity_id']]
        analysis_claims.append({'id': claim['id'], 'identity_group': prior['id'], 'year': claim['year'], 'identity_available_year': prior['available_year'], 'layer': claim['era'], 'category': claim['category'], 'candidates': [{'species': c['species_id'], 'probability': c['probability']} for c in prior['candidates']]})
        sources.append({'claim_id':claim['id'],'source_id':claim['source_id'],'source_url':claim['source_url'],'sha256':claim['source_sha256'],'span_start':claim['span_start'],'span_end':claim['span_end'],'reviewer':claim['reviewer']})
    for row in grades:
        validate_grade(row)
        from extract.claims import CATEGORIES
        if row['category'] not in CATEGORIES:
            raise ValueError('Evidence category outside prespecified schema')
        if not row['reviewed'] or not row.get('reviewer'):
            raise ValueError('Grades must be human-reviewed before ingestion')
        if row.get('study_type') != 'original':
            raise ValueError('Reviews cannot establish original confirmation years')
        if not re.fullmatch(r'[a-f0-9]{64}', row.get('record_sha256','')):
            raise ValueError('Grade needs a valid SHA-256 of its retrieved evidence record')
        record_path = (root / row['record_path']).resolve()
        if not record_path.is_relative_to(root.resolve()):
            raise ValueError('Evidence record path must stay within the project')
        if hashlib.sha256(record_path.read_bytes()).hexdigest() != row['record_sha256']:
            raise ValueError('Evidence record hash mismatch')
    strict = build_ledger(grades)
    vitro = {(r['species_id'],r['category']):r for r in build_ledger(grades, allow_in_vitro=True)}
    ledger = []
    for row in strict:
        key=(row['species_id'],row['category'])
        ledger.append({'species':row['species_id'],'category':row['category'],'tested_year':row['tested_year'],'confirmed_year':row['confirmed_year'],'refuted_year':row['refuted_year'],'in_vitro_confirmed_year':vitro[key]['confirmed_year'],'pmids':row['pmids']})
    for row in effort:
        if not row.get('query') or not row.get('synonym_version') or not row.get('coverage_reviewed'):
            raise ValueError('Effort needs query, synonym version and coverage review')
    dataset = {'observation_end':coverage['observation_end'],'claims':analysis_claims,'ledger':ledger,'taxa':accepted_taxa,'effort':[{'species':r['species_id'],'year':r['year'],'count':r['count']} for r in effort], 'coverage':coverage,'test_coverage':coverage.get('pairs',[]),'claim_provenance':sources,'evidence_provenance':[{'pmid':r['pmid'],'record_sha256':r['record_sha256'],'reviewer':r['reviewer']} for r in grades]}
    validate_dataset(dataset)
    return dataset


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviewed',type=Path,default=ROOT/'data/reviewed')
    parser.add_argument('--output',type=Path,default=ROOT/'data/derived/dataset.json')
    args=parser.parse_args()
    result=build(args.reviewed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(f'Validated dataset: {len(result["claims"])} claims, {len(result["ledger"])} tested pairs')

if __name__=='__main__': main()
