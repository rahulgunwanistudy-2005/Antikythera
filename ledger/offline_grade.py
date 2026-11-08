"""Conservative offline abstract cues for human-review proposals.

This is a transparent rule baseline, not an evidence classifier with measured
accuracy. It never creates a reviewed grade or first-confirmation label.
Cue offsets refer to the exact original abstract string, including markup.
"""
import hashlib,re
from ledger.queries import MODERN
METHOD='offline_cue_baseline'
CAVEATS=[
    'Heuristic suggestions require independent human reading of the original study.',
    'A word match does not establish the studied species, preparation, endpoint or causal result.',
    'No extraction accuracy, grading performance or medical effect is claimed.',
    'Species synonyms and abbreviated names are not resolved by this baseline.',
    'Evidence tier and preparation scope can differ across experiments in one abstract.'
]

def _hits(pattern,text,label,flags=re.I):
    return [{'label':label,'start':m.start(),'end':m.end()} for m in re.finditer(pattern,text,flags)]

def _sentence(text,start):
    # Sentence detection retains raw offsets and is only a conservative cue gate.
    left=max(text.rfind('.',0,start),text.rfind('!',0,start),text.rfind('?',0,start))+1
    boundaries=[v for char in '.!?' if (v:=text.find(char,start))>=0]
    right=min(boundaries)+1 if boundaries else len(text)
    return left,right,text[left:right]

def suggest(record,species_id,category):
    abstract=record.get('abstract','') or ''
    if not isinstance(abstract,str):raise ValueError('Abstract must be a string')
    if category not in MODERN:raise ValueError('Unknown indication category')
    if not isinstance(species_id,str) or not species_id.strip():raise ValueError('Species name required')
    digest=hashlib.sha256(abstract.encode('utf-8')).hexdigest();spans=[]
    def hits(pattern,label):
        result=_hits(pattern,abstract,label);spans.extend(result);return result
    target=hits(r'\b'+re.escape(species_id.strip())+r'\b','target_species')
    category_pattern=r'\b(?:'+'|'.join(re.escape(t) for t in MODERN[category])+r')\w*\b'
    topic=hits(category_pattern,'category_topic')
    extract=hits(r'\b(?:extracts?|decoctions?|infusions?|whole[- ]plant|plant preparations?|leaf powder|root powder)\b','botanical_preparation')
    compound=hits(r'\b(?:(?:purified|isolated)\s+(?:bioactive\s+)?(?:compounds?|alkaloids?|molecules?)|pure\s+(?:colchicine|galantamine|morphine|paclitaxel|vinblastine|vincristine|metformin))\b','isolated_compound')
    compound_names=hits(r'\b(?:colchicine|galantamine|morphine|paclitaxel|vinblastine|vincristine|metformin)\b','named_compound')
    treatment=hits(r'\b(?:administered|treated with|treatment with|received|given|dosed|oral administration|injected|incubated with)\b','intervention')
    in_vitro=hits(r'\b(?:in vitro|cell lines?|cell cultures?|cultured cells|macrophages?|fibroblasts?|enzyme assay|enzyme inhibition|IC(?:50|<sub>50</sub>))\b','in_vitro')
    animal=hits(r'\b(?:rats?|mice|in vivo|animal model|murine model|Wistar|Sprague.Dawley)\b','in_vivo')
    clinical=hits(r'\b(?:randomized|randomised|double.blind|placebo.controlled)\b','clinical_design')
    patient=hits(r'\b(?:patients?|participants?|volunteers?)\b','human_participants')
    experiment=hits(r'\b(?:control group|controls?|randomly assigned|randomized|randomised|dose.dependent|compared with|compared to)\b','experimental_design')
    result=hits(r'\b(?:significantly|p\s*[<≤]\s*0[.,]0[0-9]|p\s*=\s*0[.,]0[0-9])','statistical_result')
    negation=hits(r'\b(?:not|no|neither|without|failed|may|might|could|potential|suggest|suggested)\b','qualification_or_negation')
    publication_types=' '.join(str(v) for v in record.get('publication_types',[])).lower()
    title=record.get('title','') or ''
    is_review=bool(re.search(r'\breview\b|meta.analysis',publication_types+' '+title,re.I)) or bool(re.search(r'\b(?:this review|we review|systematic review|meta.analysis)\b',abstract,re.I))
    is_case='case report' in publication_types or bool(re.search(r'\bcase report\b',title,re.I))
    study_type='review' if is_review else 'case_report' if is_case else 'original' if experiment and treatment else 'unclear'
    # A target name and extract cue must be nearby, not isolated mentions of
    # unrelated plants elsewhere in a multi-species abstract.
    target_preparation=bool(target and extract and any(abs(a['start']-b['start'])<=180 for a in target for b in extract))
    scope='unclear'
    if compound and not target_preparation:scope='compound_only'
    elif target_preparation and not compound and not compound_names:scope='botanical'
    elif compound_names and not extract:scope='compound_only'
    tiers=[]
    if in_vitro:tiers.append('in_vitro')
    if animal:tiers.append('in_vivo')
    if clinical and patient:tiers.append('clinical')
    tier=tiers[0] if len(tiers)==1 else None
    verdict=None;rationale=[];abstain=True
    if not abstract:rationale.append('No abstract available.')
    if not target:rationale.append('Exact target species is absent from the abstract.')
    if not topic:rationale.append('No prespecified category cue in the abstract.')
    if is_review:rationale.append('Review article cues exclude original experimental confirmation.')
    if is_case:rationale.append('Case-report cues require individual human interpretation.')
    if scope!='botanical':rationale.append('Botanical intervention scope is unresolved or compound-only.')
    if len(tiers)>1:rationale.append('More than one possible evidence tier appears.')
    if not tiers:rationale.append('No sufficiently explicit experimental evidence-tier cue.')
    # Narrow positive endpoints. Direction is explicitly required, rather than
    # assigning support from any favorable verb anywhere in an abstract.
    endpoints={
        'joint':r'(?:inflammation|paw edema|paw oedema|joint swelling|arthritic score)',
        'metabolic':r'(?:blood glucose|blood sugar|hyperglyc(?:emia|aemia))',
        'neuro':r'(?:pain|writhing|nociception)'
    }
    endpoint=endpoints.get(category)
    if target and topic and scope=='botanical' and study_type=='original' and tier and result and endpoint:
        positive=hits(r'\b(?:significantly\s+)?(?:reduced|decreased|alleviated|inhibited)\b[^.!?]{0,70}\b'+endpoint+r'\b','directional_endpoint_result')
        negative=hits(r'\b(?:did not|failed to)\s+(?:significantly\s+)?(?:reduce|decrease|alleviate|inhibit)\b[^.!?]{0,70}\b'+endpoint+r'\b','explicit_negative_endpoint')
        choices=[('refutes',m) for m in negative]+[('supports',m) for m in positive]
        qualified=[]
        for proposed,cue in choices:
            left,right,sentence=_sentence(abstract,cue['start'])
            # Require an explicit botanical intervention in the result sentence.
            # A reference to an isolated drug or to an unrelated discussion is
            # insufficient. The species link and study-design gates also hold.
            has_preparation=any(left<=p['start']<right for p in extract)
            has_statistics=any(left<=p['start']<right for p in result)
            has_hedge=bool(re.search(r'\b(?:may|might|could|potential|suggest(?:ed)?)\b',sentence,re.I))
            negated_positive=proposed=='supports' and bool(re.search(r'\b(?:not|no|failed|neither)\b',sentence,re.I))
            if has_preparation and has_statistics and not has_hedge and not negated_positive:qualified.append(proposed)
        if qualified and len(set(qualified))==1:
            verdict=qualified[0];abstain=False
            rationale.append('A narrow directional endpoint, statistical result and botanical preparation co-occur in an experimental result sentence. This remains an unreviewed suggestion.')
        elif qualified:rationale.append('Conflicting positive and negative result cues require adjudication.')
    if verdict is None:rationale.append('The conservative result-linkage gate abstains. Read the complete abstract and original study.')
    return {'verdict':verdict,'evidence_tier':tier,'preparation_scope':scope,'study_type':study_type,'rationale':' '.join(rationale),'method':METHOD,'abstain':abstain,'reviewed':False,'abstract_sha256':digest,'evidence_spans':sorted(spans,key=lambda s:(s['start'],s['end'],s['label'])),'caveats':list(CAVEATS),'version':'offline-abstract-cues-2026-11-07-v1'}
