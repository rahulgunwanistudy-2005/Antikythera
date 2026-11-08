"""Check catalog source links without declaring their scientific claims verified."""
import argparse, json, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def check(url):
    try:
        with urlopen(Request(url,method='HEAD',headers={'User-Agent':'Antikythera-source-check/0.1'}),timeout=20) as r:
            return {'url':url,'http_status':r.status,'reachable':True,'content_verified':False,'final_url':r.url}
    except HTTPError as e: return {'url':url,'http_status':e.code,'reachable':False,'content_verified':False}
    except (URLError,TimeoutError):return {'url':url,'http_status':None,'reachable':False,'content_verified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--catalog',default='data/seed/catalog.json');p.add_argument('--output',default='data/derived/link_checks.json');a=p.parse_args()
    data=json.loads(Path(a.catalog).read_text());urls=sorted({s['url'] for plant in data['plants'] for s in plant['sources']})
    rows=[]
    for url in urls:rows.append(check(url));time.sleep(.4)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps({'checked_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'results':rows},indent=2))
    print(json.dumps({'links':len(rows),'reachable':sum(r['reachable'] for r in rows),'output':a.output}))
