"""Conservative rule proposals, never audited extraction or efficacy labels."""
import hashlib,re
from harmonise.baseline import Harmoniser
from harmonise.categories import PHRASES
from extract.chapters import culpeper_chapters

# These cues only gate candidate sentences. Negation and contextual meaning
# remain explicit human-review tasks.
THERAPY=re.compile(r'\b(help\w*|cure\w*|heal\w*|remed\w*|good|eas\w*|provok\w*|expel\w*|kill\w*|cleans\w*|staunch\w*|stopp\w*|stay\w*|effectual|against|reliev\w*|assuag\w*|mollif\w*)\b',re.I)

def extract_culpeper(text,source,path,raw_hash):
    harmoniser=Harmoniser();proposals=[];chapters=culpeper_chapters(text)
    for chapter in chapters:
        body=text[chapter['start']:chapter['end']]
        gov=re.search(r'_Government and virtues?\._\]',body,re.I)
        if not gov:continue
        start=chapter['start']+gov.end();section=text[start:chapter['end']]
        for sentence in re.finditer(r'[^.!?]+(?:[.!?]+|$)',section):
            raw=sentence.group();left=len(raw)-len(raw.lstrip());right=len(raw.rstrip())
            a=start+sentence.start()+left;b=start+sentence.start()+right
            span=text[a:b]
            if len(span)<15 or not THERAPY.search(span):continue
            found=[]
            for category,phrases in PHRASES.items():
                for phrase in phrases:
                    match=re.search(r'\b'+re.escape(phrase)+r'\b',span,re.I)
                    if match:
                        found.append((category,match.group()));break
            for category,ailment in found:
                digest=hashlib.sha256(f'{source["id"]}:{a}:{b}:{category}'.encode()).hexdigest()[:18]
                mapping=harmoniser.propose(ailment)
                proposals.append({'id':'claim-'+digest,'source_id':source['id'],'source_text_path':str(path),'source_sha256':raw_hash,'source_url':source['catalog_url'],'plant_name_as_written':chapter['title'],'historical_name_context':chapter['title'],'plant_context_start':chapter['start'],'plant_context_end':chapter['title_end'],'plant_context_span':text[chapter['start']:chapter['title_end']],'part':None,'preparation':None,'ailment_as_written':ailment,'span_start':a,'span_end':b,'source_span':span,'category':category,'category_candidates':mapping['candidates'],'harmonisation':mapping,'year':None,'edition_year':source.get('edition_year'),'era':source['layer'],'reviewed':False,'historical_date_reviewed':False,'licence_reviewed':False,'identity_id':None,'method':'therapeutic_cue_and_ailment_lexicon_v1','status':'proposed','review_blockers':['historical_date','identity','source_interpretation','negation_and_scope','licence_jurisdiction'],'analysis_eligible':False})
    return chapters,proposals
