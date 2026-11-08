"""Atomic, resumable public-API cache. Offline mode never opens a socket."""
import hashlib, json, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request,urlopen

class CacheMiss(RuntimeError): pass

class JsonCache:
    def __init__(self,path,offline=True,delay=.4):
        self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
        self.offline=offline;self.delay=delay;self.last=0
    def get(self,url):
        key=hashlib.sha256(url.encode()).hexdigest();path=self.path/(key+'.json')
        if path.exists():
            saved=json.loads(path.read_text());return saved['data'],saved,path
        if self.offline:raise CacheMiss('Public API cache miss')
        for attempt in range(4):
            time.sleep(max(0,self.delay-(time.monotonic()-self.last)));self.last=time.monotonic()
            try:
                with urlopen(Request(url,headers={'User-Agent':'Antikythera-research/0.2','Accept':'application/json'}),timeout=45) as response:
                    data=json.load(response)
                saved={'url':url,'fetched_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'data':data}
                temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(saved,ensure_ascii=False));temporary.replace(path)
                return data,saved,path
            except HTTPError as error:
                if error.code not in (429,500,502,503,504):raise RuntimeError('Public API returned HTTP '+str(error.code)) from None
            except (URLError,TimeoutError):pass
            time.sleep(min(8,2**attempt))
        raise RuntimeError('Public API request failed after retries')
