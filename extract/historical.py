"""Source-specific manuscript proposal adapters with explicit text-layer gates."""
import hashlib,re
from extract.baseline import THERAPY
from harmonise.baseline import Harmoniser
from harmonise.categories import PHRASES
GERMAN={
'urinary':['Harn','Blase','Nieren','Nierenleiden','Wassersucht'], 'gi':['Magen','Magenschmerzen','Leber','Leberleiden','Gelbsucht','Bauch','Darm','Durchfall','Blähungen'],
'skin':['Wunden','Geschwüre','Geschwüren','Haut','Krätze','Verbrennungen'], 'respiratory':['Husten','Lunge','Brust','Athem','Asthma'],
'neuro':['Schmerzen','Kopfschmerzen','Epilepsie','Schlaf','Nerven'], 'joint':['Podagra','Gicht','Gelenke','Entzündungen'],
'cardiovascular':['Herz','Herzklopfen'],'metabolic':['Durst','Diabetes'],'gynaecological':['Gebärmutter','Menstruation','Geburt','Frauen'],
'infection':['Fieber','Würmer','Pest'],'eye':['Augen','Augenleiden','Augenlider'],'poison':['Gift','Gifte','Gegengift','Gegengifte','Schlangen']}
GERMAN_CUE=re.compile(r'helf\w*|heilt?\w*|gegen|linder\w*|treib\w*|wirk\w*|nütz\w*|gut|heilsam|heilkräft\w*',re.I)

def berendes_chapters(text):
    matches=list(re.finditer(r'(?m)^[ \t]*(?:Cap|Gap|Oap|Cajp)\.?[ \t]+\d+\.[^\n]{0,170}',text))
    result=[]
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        chunk=text[m.end():end]
        # Footnote marker is a conservative boundary, not a scholarly edition.
        foot=re.search(r"(?m)^[ \t]*(?:[’']\)|[’']?\d+\)|[’']I[ \t])",chunk)
        prefix_end=m.end()+foot.start() if foot else end
        result.append({'title':m.group().strip(),'start':m.start()+len(m.group())-len(m.group().lstrip()),'title_end':m.end(),'end':end,'body_start':m.end(),'body_end':prefix_end,'text_layer':'translated_original_prefix_heuristic' if foot else 'original_commentary_boundary_unresolved'})
    return result

def paul_chapters(text):
    matches=[]
    entry_section=re.search(r'ON\s+THE\s+POWERS\s+OF\s+SIMPLES\s+INDIVIDUALLY',text,re.I)
    if not entry_section:return []
    for m in re.finditer(r'(?m)^([^\n]{1,90})\n([A-Z][A-Za-z][A-Za-z -]{1,45}),',text):
        prev=m.group(1).strip()
        if not prev.endswith(',') or len(prev.split())>4:continue
        if m.start()<entry_section.end():continue # Introductory essays have no plant entry.
        matches.append(m)
    result=[]
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        comm=re.search(r'Commentary\.',text[m.end():min(end,m.end()+20000)],re.I)
        if not comm:continue # Fail closed when translation/commentary separator is lost.
        result.append({'title':m.group(2),'start':m.start(2),'title_end':m.end(2),'end':end,'body_start':m.end(2),'body_end':m.end()+comm.start(),'text_layer':'translation_before_explicit_commentary_marker'})
    return result

def propose_manuscript(text,source,path,digest):
    german=source['layer']=='dioscorides';chapters=berendes_chapters(text) if german else paul_chapters(text)
    lexicon=GERMAN if german else PHRASES;cue=GERMAN_CUE if german else THERAPY;rows=[];mapper=Harmoniser()
    for c in chapters:
        section=text[c['body_start']:c['body_end']]
        for sentence in re.finditer(r'[^.!?]+(?:[.!?]+|$)',section):
            raw=sentence.group();a=c['body_start']+sentence.start()+len(raw)-len(raw.lstrip());b=c['body_start']+sentence.start()+len(raw.rstrip());span=text[a:b]
            if len(span)<20 or not cue.search(span):continue
            for category,phrases in lexicon.items():
                ailment=next((m.group() for phrase in phrases if (m:=re.search(r'\b'+re.escape(phrase)+r'\b',span,re.I))),None)
                if not ailment:continue
                identifier='claim-'+hashlib.sha256(f'{source["id"]}:{a}:{b}:{category}'.encode()).hexdigest()[:18]
                mapping=mapper.propose(ailment) if not german else {'method':'german_ailment_lexicon_baseline_v1','candidates':[{'category':category,'score':1.0}],'calibrated':False,'requires_adjudication':True}
                rows.append({'id':identifier,'source_id':source['id'],'source_text_path':str(path),'source_sha256':digest,'source_url':source['catalog_url'],'plant_name_as_written':c['title'],'historical_name_context':c['title'],'plant_context_start':c['start'],'plant_context_end':c['title_end'],'plant_context_span':text[c['start']:c['title_end']],'part':None,'preparation':None,'ailment_as_written':ailment,'span_start':a,'span_end':b,'source_span':span,'category':category,'category_candidates':mapping['candidates'],'harmonisation':mapping,'year':None,'edition_year':source['edition_year'],'era':source['layer'],'reviewed':False,'historical_date_reviewed':False,'licence_reviewed':False,'identity_id':None,'method':'manuscript_lexicon_baseline_v1','text_layer':c['text_layer'],'status':'proposed','review_blockers':['ocr_quality','source_commentary_boundary','historical_date','identity','botanical_vs_nonbotanical','translation','negation_and_scope'],'analysis_eligible':False})
    return chapters,rows
