"""Licensed JATS medicinal-table import, preserving original XML provenance."""
import hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as ET
from harmonise.baseline import Harmoniser

def expanded_grid(table):
    active={};rows=[]
    for row in table.findall('.//tr'):
        result={col:cell for col,(remaining,cell) in active.items()};next_active={col:(remaining-1,cell) for col,(remaining,cell) in active.items() if remaining>1};col=0
        for cell in row:
            if cell.tag not in ('td','th'):continue
            while col in result:col+=1
            colspan=int(cell.get('colspan','1'));rowspan=int(cell.get('rowspan','1'))
            for c in range(col,col+colspan):
                result[c]=cell
                if rowspan>1:next_active[c]=(rowspan-1,cell)
            col+=colspan
        rows.append(result);active=next_active
    return rows

def medicinal_table(xml_path,source,root):
    root=Path(root);xml_path=Path(xml_path);raw=xml_path.read_bytes();tree=ET.fromstring(raw)
    licence=' '.join(''.join(n.itertext()) for n in tree.findall('.//permissions'))
    if 'creativecommons.org/licenses/by/2.0' not in licence:raise ValueError('Expected source-specific CC BY2.0 declaration missing')
    table=tree.find('.//table-wrap[@id="T2"]')
    if table is None:raise ValueError('Medicinal table T2 missing')
    rows=expanded_grid(table);entries=[];last_taxon=None;seen=set()
    clean=lambda cell:' '.join(''.join(cell.itertext()).split()) if cell is not None else ''
    for number,row in enumerate(rows[1:],2):
        first=row.get(0);italic=first.find('italic') if first is not None else None
        if italic is not None:last_taxon=clean(italic)
        elif clean(first) and not italic is not None:
            # Family and voucher lines share a use via rowspans but are not taxa.
            value=clean(first)
            if value.endswith('aceae') or re.match(r'^(CAME|PRN|GEO)\s',value):continue
            if value.strip():continue
        if not last_taxon:continue
        use=clean(row.get(5));part=clean(row.get(4))
        if not use or use.startswith('Recorded modalities'):continue
        key=(last_taxon,part,use)
        if key in seen:continue
        seen.add(key);entries.append({'taxon':last_taxon,'part':part,'use':use,'table_row':number})
    # Store a canonical, whitelisted text projection. Exact character spans
    # reference this projection; original XML hash and table row retain lineage.
    text=''.join(f'{e["taxon"]}\t{e["part"]}\t{e["use"]}\n' for e in entries)
    path=root/'data/raw/cache/texts/balkan-open-access-normalised.txt';path.write_text(text)
    digest=hashlib.sha256(path.read_bytes()).hexdigest();mapper=Harmoniser();proposals=[];offset=0
    for e in entries:
        line=f'{e["taxon"]}\t{e["part"]}\t{e["use"]}';mapping=mapper.propose(e['use']);category=mapping['candidates'][0]['category']
        identifier='claim-'+hashlib.sha256(f'{source["id"]}:{offset}:{category}'.encode()).hexdigest()[:18]
        proposals.append({'id':identifier,'source_id':source['id'],'source_text_path':str(path.relative_to(root)),'source_sha256':digest,'source_url':source['catalog_url']+'#T2','original_source_path':str(xml_path.relative_to(root)),'original_source_sha256':hashlib.sha256(raw).hexdigest(),'source_table_row':e['table_row'],'plant_name_as_written':e['taxon'],'historical_name_context':e['taxon'],'part':e['part'] or None,'preparation':None,'ailment_as_written':e['use'],'span_start':offset,'span_end':offset+len(line),'source_span':line,'category':category,'category_candidates':mapping['candidates'],'harmonisation':mapping,'year':2014,'edition_year':2014,'era':'balkan','reviewed':False,'historical_date_reviewed':False,'licence_reviewed':False,'licence':'CC-BY-2.0','licence_url':'https://creativecommons.org/licenses/by/2.0/','attribution':'Pieroni et al. 2014, doi:10.1186/1746-4269-10-31, medicinal Table2. Normalised by Antikythera; community columns omitted.','identity_id':None,'method':'licensed_jats_table_rowspan_projection_v1','status':'proposed','review_blockers':['category','multiple_taxa_rowspan','botanical_vs_nonbotanical','human_vs_veterinary','ritual_vs_pharmacological'],'analysis_eligible':False})
        offset+=len(line)+1
    metadata={'projection':'Taxon/plant-part/medicinal-use only. Folk names, group indicators, localities and participant fields excluded.','original_sha256':hashlib.sha256(raw).hexdigest(),'licence':'CC-BY-2.0','attribution':'Pieroni et al. 2014','table_id':'T2','rows':len(entries)}
    path.with_suffix('.metadata.json').write_text(json.dumps(metadata,indent=2))
    return entries,proposals
