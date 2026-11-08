"""Build an attributed reference from licensed Lardos article Table2.

This does not acquire Figshare file11 or establish independent identity truth.
"""
import hashlib,json,re
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
SOURCE_URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC7615571/'
DOI='10.1016/j.jep.2023.117622'

def build(xml_path):
    raw=Path(xml_path).read_bytes();root=ET.fromstring(raw)
    licence=' '.join(''.join(n.itertext()) for n in root.findall('.//license'))
    if 'creativecommons.org/licenses/by/4.0' not in licence:raise ValueError('Expected article CC BY4.0 licence not present')
    table=root.find('.//table-wrap[@id="T2"]')
    if table is None:raise ValueError('Table2 not found')
    text=lambda element:' '.join(' '.join(element.itertext()).split())
    rows=[];unparsed=[]
    columns={4:'strong',5:'moderate',6:'weak',7:'not_assessed_in_FT_or_FC'}
    groups=[]
    for index,row in enumerate(table.findall('.//tr')[1:],2):
        cells=row.findall('td')
        if len(cells)!=8:raise ValueError('Unexpected Table2 row structure at row '+str(index))
        values=[text(cell).replace('(continued on next page )','').strip() for cell in cells]
        if values[0].startswith('JCLP_'):groups.append({'start_row':index,'source_rows':[index],'cells':values})
        elif groups:
            groups[-1]['source_rows'].append(index)
            for col in (1,2,4,5,6,7):
                if values[col]:groups[-1]['cells'][col]+=' '+values[col]
    for group in groups:
        values=group['cells'];index=group['start_row'];lemma,jc,dmm,expected=values[:4];parsed=0
        for col,grade in columns.items():
            literal=' '.join(values[col].split())
            if not literal:continue
            matches=list(re.finditer(r'(.*?)\(([0-3])\)',literal,re.S))
            end=0
            for match in matches:
                candidate=' '.join(match.group(1).split())
                if not candidate:continue
                parsed+=1;end=match.end()
                rows.append({'id':f'lardos-table2-row{index}-candidate{parsed}','lemma_tag':lemma,'historical_name_jc':jc,'historical_name_dmm':dmm,'candidate_name_as_published':candidate,'botanical_congruence_grade':grade,'medicinal_congruence_grade_ordinal':int(match.group(2)),'source_table':'Table2','source_row':index,'source_rows':group['source_rows'],'source_column':col+1,'source_cell_text':literal,'source_url':SOURCE_URL+'#T2','source_doi':DOI,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_licence':'CC-BY-4.0','identity_probability':None,'identity_truth_label':None,'antikythera_prediction':None,'eligible_for_ece':False,'independent_gold':False,'interpretation_status':'published_congruence_reference_only'})
            remaining=literal[end:].strip()
            if remaining:
                parsed+=1
                rows.append({'id':f'lardos-table2-row{index}-candidate{parsed}','lemma_tag':lemma,'historical_name_jc':jc,'historical_name_dmm':dmm,'candidate_name_as_published':remaining,'botanical_congruence_grade':grade,'medicinal_congruence_grade_ordinal':None,'medicinal_grade_missing_in_xml':True,'source_table':'Table2','source_row':index,'source_rows':group['source_rows'],'source_column':col+1,'source_cell_text':literal,'source_url':SOURCE_URL+'#T2','source_doi':DOI,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_licence':'CC-BY-4.0','identity_probability':None,'identity_truth_label':None,'antikythera_prediction':None,'eligible_for_ece':False,'independent_gold':False,'interpretation_status':'published_congruence_reference_only'})
                unparsed.append({'row':index,'column':col+1,'text':remaining,'note':'Candidate preserved from botanical grade column; medicinal ordinal missing in XML, retained null.'})
        if expected.isdigit() and int(expected)!=parsed:unparsed.append({'row':index,'expected_candidates':int(expected),'parsed_candidates':parsed})
    return {'schema_version':1,'status':'published_article_reference_figshare_unavailable','attribution':'Lardos, Patmore, Allkin, Lazarou, Nesbitt, Scott and Zipser (2024), Journal of Ethnopharmacology322:117622. Table2 transformed to JSON by Antikythera.','source_url':SOURCE_URL,'source_doi':DOI,'source_licence':'CC-BY-4.0','licence_url':'https://creativecommons.org/licenses/by/4.0/','source_cache_path':str(Path(xml_path).relative_to(ROOT)),'source_sha256':hashlib.sha256(raw).hexdigest(),'candidate_count':len(rows),'lemma_count':len({r['lemma_tag'] for r in rows}),'botanical_grade_counts':dict(Counter(r['botanical_congruence_grade'] for r in rows)),'grade_definitions':{'botanical_congruence':{'strong':'Published total botanical comparison score >=5.','moderate':'Published total botanical comparison score3–4.','weak':'Published total botanical comparison score<3.','not_assessed_in_FT_or_FC':'Candidate absent from the compared Flora of Turkey or Flora of Cyprus.'},'medicinal_congruence_ordinal':{'3':'strong comparison congruence','2':'moderate comparison congruence','1':'weak comparison congruence','0':'No comparable medicinal-use data in the selected modern sources.'}},'warnings':['Published congruence grades are not confirmed historical identities, outcome labels or probabilities.','The paper uses medicinal-use similarity as supplementary evidence. Reusing those grades to validate medicinal prediction would risk circularity.','This reference is ArticleTable2, not the inaccessible Figshare research data file11.','No Antikythera predictions are paired with reference records. No identity ECE or completed human audit follows from this acquisition.','Only the information-rich historical subset appears here. Selection limits generalisation.','Scientific names and historical strings remain as published. No modern taxonomy remapping is implied.'],'unparsed_or_count_mismatches':unparsed,'records':rows}

if __name__=='__main__':
    p=ROOT/'data/raw/cache/identity_expert/article.xml';data=build(p);out=Path(__file__).with_name('candidate_reference.json');out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:data[k] for k in ('candidate_count','lemma_count','botanical_grade_counts','unparsed_or_count_mismatches')},ensure_ascii=False))
