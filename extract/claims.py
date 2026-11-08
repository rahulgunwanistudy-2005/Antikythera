"""Validate source-grounded extraction; no model is run implicitly."""
import json, re
CATEGORIES = ('urinary','gi','skin','respiratory','neuro','joint','cardiovascular','metabolic','gynaecological','infection','eye','poison')

def chunks(text, max_chars=10000):
    """Preserve exact absolute offsets; split on headings where possible."""
    if max_chars < 1: raise ValueError('max_chars must be positive')
    boundaries=[0]+[m.start() for m in re.finditer(r'(?m)^#{1,4} |^CHAPTER ',text) if m.start()>0]+[len(text)]
    for left,right in zip(boundaries,boundaries[1:]):
        for start in range(left,right,max_chars):
            end=min(start+max_chars,right)
            yield {'start':start,'end':end,'text':text[start:end]}

def validate_claim(claim, source_text):
    for key in ('id','source_id','plant_name_as_written','ailment_as_written','part','preparation','span_start','span_end','source_span','category','year','era'):
        if key not in claim: raise ValueError('Missing '+key)
    a,b=claim['span_start'],claim['span_end']
    if type(a) is not int or type(b) is not int or not (0<=a<b<=len(source_text)): raise ValueError('Invalid absolute source offsets')
    if source_text[a:b] != claim['source_span']: raise ValueError('Source span does not match offsets')
    for key in ('plant_name_as_written','ailment_as_written'):
        if not claim[key]: raise ValueError(key+' is empty')
        if claim[key].casefold() in claim['source_span'].casefold(): continue
        if key != 'plant_name_as_written': raise ValueError(key+' is not in source span')
        ca,cb=claim.get('plant_context_start'),claim.get('plant_context_end')
        context=claim.get('plant_context_span')
        if type(ca) is not int or type(cb) is not int or not 0<=ca<cb<=len(source_text): raise ValueError('Plant name absent and no valid chapter context')
        if context!=source_text[ca:cb] or claim[key].casefold() not in context.casefold() or ca>a: raise ValueError('Plant chapter context mismatch')
    if claim['category'] not in CATEGORIES: raise ValueError('Unknown category')
    if type(claim['year']) is not int: raise ValueError('year must be an integer')
    if not isinstance(claim['id'],str) or not claim['id']: raise ValueError('id required')
    return claim

if __name__=='__main__':
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser();p.add_argument('text');p.add_argument('claims');args=p.parse_args()
    source=Path(args.text).read_text(); claims=json.loads(Path(args.claims).read_text())
    for claim in claims: validate_claim(claim,source)
    print(json.dumps({'validated':len(claims)}))
