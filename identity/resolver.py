"""Versioned taxonomic candidates. Service confidence is not identity probability."""
from urllib.parse import urlencode
from ledger.cache import JsonCache
BACKBONE='d7dddbf4-2cf0-4f39-9b2a-bb099caae36c'

class Resolver:
    def __init__(self,cache,offline=True):self.cache=JsonCache(cache,offline)
    def resolve(self,name):
        meta,ms,mp=self.cache.get('https://api.gbif.org/v1/dataset/'+BACKBONE)
        url='https://api.gbif.org/v1/species/match?'+urlencode({'name':name,'verbose':'true','kingdom':'Plantae'})
        match,saved,path=self.cache.get(url)
        version=str(meta.get('version') or meta.get('modified') or ms['fetched_at'])
        candidates=[]
        for row in [match,*match.get('alternatives',[])]:
            if row.get('rank')!='SPECIES' or row.get('matchType')=='NONE':continue
            # Accepted species field supplies accepted name for synonym records.
            species=row.get('species') or row.get('canonicalName')
            if not species or species in {c['species_id'] for c in candidates}:continue
            candidates.append({'species_id':species,'family':row.get('family'),'probability':None,'taxonomy_usage_key':row.get('acceptedUsageKey') or row.get('usageKey'),'name_match_score':row.get('confidence'),'name_match_type':row.get('matchType'),'note':'Name-match score does not quantify historical identity certainty.'})
        return {'id':'taxon-'+str(match.get('usageKey','unresolved'))+'-'+name.replace(' ','-').lower(),'query_name':name,'species_id':candidates[0]['species_id'] if candidates else name,'family':candidates[0]['family'] if candidates else None,'backbone_version':'GBIF '+version,'backbone_dataset_key':BACKBONE,'backbone_doi':meta.get('doi'),'licence':meta.get('license'),'source_url':url,'record_path':str(path),'metadata_path':str(mp),'candidates':candidates,'reviewed':False,'status':'candidate' if candidates else 'unresolved','historical_identity_probability':None,'available_year':None,'review_blockers':['historical_name_link','regional_presence','expert_identity','temporal_prior']}
