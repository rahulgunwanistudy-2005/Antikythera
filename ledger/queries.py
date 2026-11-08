"""Versioned search plans, including unclaimed categories for future nulls."""
from harmonise.categories import LEXICON
VERSION='category-query-plan-2026-11-07-v1'
# Modern terms intentionally reviewed separately from historical language.
MODERN={
'urinary':['diuretic','urinary','renal','kidney'], 'gi':['gastrointestinal','gastric','intestinal','diarrhea','liver'],
'skin':['wound','skin','dermatitis','ulcer'],'respiratory':['asthma','respiratory','cough','lung'],
'neuro':['analgesic','pain','neuroprotective','cognition','epilepsy'], 'joint':['arthritis','gout','inflammation','anti-inflammatory'],
'cardiovascular':['cardiovascular','cardiac','hypertension'], 'metabolic':['diabetes','glucose','hypoglycemic'],
'gynaecological':['uterine','menstrual','reproductive','gynecological'],'infection':['antimicrobial','antibacterial','antiviral','infection'],
'eye':['ocular','ophthalmic','retina'],'poison':['toxicology','poisoning','antidote','venom']}

def literal(value):return '"'+value.replace('"','')+'"'
def plan(species_id,synonyms=()):
    names=sorted(set([species_id,*synonyms]));ep='('+' OR '.join('TITLE_ABS:'+literal(n) for n in names)+')'
    pm='('+' OR '.join(literal(n)+'[Title/Abstract]' for n in names)+')'
    return [{'species_id':species_id,'category':category,'version':VERSION,'synonym_version':'accepted-name-only-v1' if not synonyms else 'explicit-synonyms-v1','europepmc_query':ep+' AND ('+' OR '.join('TITLE_ABS:'+literal(t) for t in terms)+') AND SRC:MED','pubmed_query':pm+' AND ('+' OR '.join(literal(t)+'[Title/Abstract]' for t in terms)+')','filter_note':'Broad query; original-study, pharmacology and preparation filters require evidence grading.'} for category,terms in MODERN.items()]
