"""Official Europe PMC API fallback requiring no invented NCBI contact.

Docs: https://europepmc.org/RestfulWebService . Abstracts stay private in
ignored raw cache. No acquired abstract implies permission to redistribute.
"""
import hashlib,json
from urllib.parse import urlencode
from ledger.cache import JsonCache
BASE='https://www.ebi.ac.uk/europepmc/webservices/rest/'

class EuropePMC:
    def __init__(self,cache,offline=True):self.cache=JsonCache(cache,offline)
    def search(self,query,max_records=25):
        if type(max_records) is not int or not 1<=max_records<=10000:raise ValueError('Cap must be between 1 and 10000')
        records=[];cursor='*';seen=set();total=None;pages=[]
        while len(records)<max_records:
            size=min(100,max_records-len(records))
            url=BASE+'search?'+urlencode({'query':query,'format':'json','resultType':'core','pageSize':size,'cursorMark':cursor})
            data,saved,path=self.cache.get(url)
            total=int(data['hitCount']);batch=data.get('resultList',{}).get('result',[]);pages.append(path)
            for row in batch:
                key=(row.get('source'),row.get('id'))
                if key in seen:raise RuntimeError('Duplicate Europe PMC pagination result')
                seen.add(key);records.append((row,saved,path))
            next_cursor=data.get('nextCursorMark')
            if not batch or not next_cursor or next_cursor==cursor or len(records)>=total:break
            cursor=next_cursor
        return {'query':query,'total_hits':total,'returned':len(records),'complete':len(records)>=total,'truncated':len(records)<total,'records':records,'pages':pages}
    def count(self,query):
        data,saved,path=self.cache.get(BASE+'search?'+urlencode({'query':query,'format':'json','resultType':'idlist','pageSize':1}))
        return int(data['hitCount']),saved,path

def _title(value):
    from html import unescape
    from html.parser import HTMLParser
    class Plain(HTMLParser):
        def __init__(self):super().__init__();self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=Plain();parser.feed(unescape(unescape(value)));return ''.join(parser.parts)

def normalise(row):
    pmid=row.get('pmid') or (row.get('id') if row.get('source')=='MED' else None)
    date=row.get('firstPublicationDate')
    year=int(date[:4]) if date and date[:4].isdigit() else int(row['pubYear']) if str(row.get('pubYear','')).isdigit() else None
    return {'pmid':pmid,'provider_id':row.get('id'),'provider_source':row.get('source'),'title':_title(row.get('title','')),'year':year,'first_publication_date':date,'date_basis':'firstPublicationDate_or_pubYear','abstract':row.get('abstractText',''),'publication_types':row.get('pubTypeList',{}).get('pubType',[]),'source_url':'https://europepmc.org/article/'+str(row.get('source'))+'/'+str(row.get('id')),'is_open_access':row.get('isOpenAccess')=='Y','licence':row.get('license'),'journal':row.get('journalInfo',{}).get('journal',{}).get('title'),'doi':row.get('doi'),'reviewed':False}
