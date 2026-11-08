"""Download a permitted manifest source, store hash and metadata, never auto-ingest."""
import argparse, hashlib, json, time
from pathlib import Path
from urllib.request import Request, urlopen

def download(source_id, output_dir, manifest=None):
    manifest=Path(manifest) if manifest else Path(__file__).with_name('sources.json')
    source=next((s for s in json.loads(manifest.read_text())['sources'] if s['id']==source_id),None)
    if not source: raise ValueError('Unknown source ID')
    if not source.get('download_allowed') or not source.get('download_url'): raise ValueError('Source not cleared for scripted download; review edition and scan terms')
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    with urlopen(Request(source['download_url'],headers={'User-Agent':'Antikythera-research/0.1'}),timeout=60) as response:
        body=response.read(); final_url=response.url
    path=output/(source_id+'.txt');path.write_bytes(body)
    metadata={'source':source,'downloaded_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'final_url':final_url,'analysis_eligible':False}
    path.with_suffix('.metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False))
    return metadata

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source_id');p.add_argument('--output',default='data/raw/cache/texts');args=p.parse_args()
    print(json.dumps(download(args.source_id,args.output),indent=2))
