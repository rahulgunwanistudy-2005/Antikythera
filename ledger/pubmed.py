"""Cached, rate-limited NCBI E-utilities acquisition. No automatic labels.

Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/
Use an NCBI contact email, especially for bulk runs. Keys stay in memory.
"""
import argparse, hashlib, json, os, re, time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET

class PubMed:
    def __init__(self, cache, email, api_key=None):
        self.cache=Path(cache);self.cache.mkdir(parents=True,exist_ok=True)
        self.email=email;self.api_key=api_key;self.last=0.0
        if not email or '@' not in email: raise ValueError('NCBI contact email required')
    def request(self, endpoint, **params):
        # Credentials never enter the hash, stored cache metadata or printed URLs.
        public={'db':'pubmed','tool':'antikythera',**params}
        key=hashlib.sha256(json.dumps([endpoint,public],sort_keys=True).encode()).hexdigest()
        path=self.cache/(key+'.json')
        if path.exists(): return json.loads(path.read_text())['body']
        payload={**public,'email':self.email}
        if self.api_key: payload['api_key']=self.api_key
        for attempt in range(5):
            time.sleep(max(0,(0.12 if self.api_key else 0.4)-(time.monotonic()-self.last)))
            self.last=time.monotonic()
            try:
                request=Request('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'+endpoint,data=urlencode(payload).encode(),headers={'User-Agent':'Antikythera/0.1'})
                with urlopen(request,timeout=45) as response: body=response.read().decode('utf-8')
                # Do not cache upstream error bodies or accidental secret echoes.
                if self.api_key and self.api_key in body: raise RuntimeError('Response contains private credential')
                if params.get('retmode')=='json':
                    parsed=json.loads(body)
                    if 'error' in parsed or parsed.get('esearchresult',{}).get('ERROR'): raise RuntimeError('NCBI search error')
                elif '<ERROR>' in body or '<Error>' in body: raise RuntimeError('NCBI XML error')
                path.write_text(json.dumps({'fetched_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'endpoint':endpoint,'query':public,'body':body},ensure_ascii=False))
                return body
            except HTTPError as error:
                if error.code not in (429,500,502,503,504): raise RuntimeError('NCBI HTTP error '+str(error.code)) from None
                retry=error.headers.get('Retry-After','')
                time.sleep(float(retry) if retry.isdigit() else min(30,2**attempt))
            except (URLError,TimeoutError): time.sleep(min(30,2**attempt))
        raise RuntimeError('NCBI request failed after retries; cached files retained')
    def count(self, query, year=None):
        args={'term':query,'retmode':'json','retmax':0}
        if year is not None: args.update(datetype='pdat',mindate='1000',maxdate=str(year))
        return int(json.loads(self.request('esearch.fcgi',**args))['esearchresult']['count'])
    def search(self, query, max_records=10000):
        if type(max_records) is not int or not 0<max_records<=10000: raise ValueError('PubMed supports at most 10,000 ESearch results; partition by year for larger searches')
        first=json.loads(self.request('esearch.fcgi',term=query,retmode='json',retmax=0))['esearchresult']
        count=int(first['count'])
        if count>max_records: raise ValueError(f'{count} matches exceed configured cap {max_records}; partition query by year rather than silently truncating')
        ids=[]
        for start in range(0,count,500):
            page=json.loads(self.request('esearch.fcgi',term=query,retmode='json',retstart=start,retmax=min(500,count-start),sort='pub_date'))['esearchresult']
            ids.extend(page['idlist'])
        if len(set(ids))!=count: raise RuntimeError('Search changed during pagination or duplicate IDs; rerun with a stable dated query')
        return ids
    def fetch(self, ids):
        if any(not str(v).isdigit() for v in ids): raise ValueError('PMIDs must be numeric')
        records=[]
        for start in range(0,len(ids),200):
            xml=self.request('efetch.fcgi',id=','.join(map(str,ids[start:start+200])),retmode='xml')
            root=ET.fromstring(xml)
            for article in root.findall('PubmedArticle'):
                citation=article.find('MedlineCitation'); meta=citation.find('Article')
                date=meta.find('Journal/JournalIssue/PubDate')
                year=date.findtext('Year') if date is not None else None
                if not year and date is not None:
                    match=re.search(r'\b(1\d{3}|20\d{2})\b',date.findtext('MedlineDate',''));year=match.group() if match else None
                text=lambda node: ''.join(node.itertext()) if node is not None else ''
                records.append({'pmid':citation.findtext('PMID'),'title':text(meta.find('ArticleTitle')),'year':int(year) if year else None,'date_basis':'journal_issue_pubdate','abstract':'\n'.join(text(n) for n in meta.findall('Abstract/AbstractText')),'publication_types':[text(n) for n in meta.findall('PublicationTypeList/PublicationType')],'status':'ungraded','source_url':'https://pubmed.ncbi.nlm.nih.gov/'+citation.findtext('PMID')+'/'})
        if {r['pmid'] for r in records} != set(map(str,ids)): raise RuntimeError('EFetch coverage incomplete; missing or non-article records require manual handling')
        return records

def species_query(names, category_query=None):
    if not names or any(not name.strip() for name in names): raise ValueError('Species names required')
    def quote(v): return '"'+v.replace('"','')+'"[Title/Abstract]'
    query='('+' OR '.join(quote(name) for name in names)+')'
    return query+' AND ('+category_query+')' if category_query else query

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--query',required=True);p.add_argument('--cache',default='data/raw/cache/pubmed');p.add_argument('--output',required=True);p.add_argument('--max-records',type=int,default=10000);a=p.parse_args()
    client=PubMed(a.cache,os.environ.get('NCBI_EMAIL',''),os.environ.get('NCBI_API_KEY'))
    ids=client.search(a.query,a.max_records);records=client.fetch(ids)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps({'query':a.query,'retrieved_count':len(records),'records':records},indent=2,ensure_ascii=False))
    print(json.dumps({'retrieved_count':len(records),'output':a.output}))
