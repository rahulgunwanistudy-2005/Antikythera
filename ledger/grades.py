"""Human/model grade schema and pair-level dated ledger construction."""
VERDICTS={'supports','refutes','irrelevant'}
TIERS={'in_vitro','in_vivo','clinical','not_applicable'}

def validate_grade(row):
    for key in ('pmid','species_id','category','year','verdict','evidence_tier','rationale','reviewed','preparation_scope'):
        if key not in row: raise ValueError('Missing '+key)
    if row['verdict'] not in VERDICTS or row['evidence_tier'] not in TIERS: raise ValueError('Invalid grade enum')
    if type(row['year']) is not int or not 1000<=row['year']<=2100: raise ValueError('Publication year required')
    if type(row['reviewed']) is not bool: raise ValueError('reviewed must be boolean')
    if row['preparation_scope'] not in ('botanical','compound_only','unclear'): raise ValueError('Invalid preparation scope')
    if not str(row['pmid']).isdigit() or not row['rationale'].strip(): raise ValueError('PMID and rationale required')
    return row

def build_ledger(grades, allow_in_vitro=False):
    """Only reviewed botanical grades; compound discoveries never count automatically."""
    grouped={}
    for row in grades:
        validate_grade(row)
        if not row['reviewed'] or row['preparation_scope']!='botanical' or row['verdict']=='irrelevant': continue
        key=(row['species_id'],row['category']);grouped.setdefault(key,[]).append(row)
    ledger=[]
    for (species,category),rows in sorted(grouped.items()):
        qualifying=[r for r in rows if r['verdict']=='supports' and (r['evidence_tier'] in ('in_vivo','clinical') or allow_in_vitro and r['evidence_tier']=='in_vitro')]
        ledger.append({'species_id':species,'category':category,'tested_year':min(r['year'] for r in rows),'confirmed_year':min((r['year'] for r in qualifying),default=None),'refuted':any(r['verdict']=='refutes' for r in rows),'refuted_year':min((r['year'] for r in rows if r['verdict']=='refutes'),default=None),'pmids':sorted(set(str(r['pmid']) for r in rows))})
    return ledger
