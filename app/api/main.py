"""Local research workspace API, versioned reviews and reproducible rebuild jobs.

Run on loopback. The private hosted app is a read-only static snapshot and never
accepts reviews. Original study abstracts are served only by this local process.
"""
from __future__ import annotations
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from fastapi import FastAPI,HTTPException,Query,Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict,Field,StrictBool
from storage.repository import Repository,Conflict,NotFound
from storage.review import validate_review,checked_path
from scripts.workspace import workspace
from timemachine import analyze

ROOT=Path(__file__).resolve().parents[2]

class ReviewRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reviewer:str=Field(min_length=2,max_length=100)
    decision:Literal['accept','reject','defer']
    note:str=Field(min_length=1,max_length=5000)
    expected_revision:int=Field(ge=0)
    attested:StrictBool
    fields:dict=Field(default_factory=dict)

class ProposalRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(min_length=1,max_length=200,pattern=r'^[a-zA-Z0-9:_-]+$')
    payload:dict

class AuditRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reviewer:str=Field(min_length=2,max_length=100)
    attested:StrictBool
    independent:StrictBool
    gold:dict
    note:str=Field(min_length=1,max_length=5000)


def create_app(root=ROOT,db_path=None,review_enabled=None):
    root=Path(root)
    repository=Repository(db_path or root/'data/local/antikythera.duckdb')
    enabled=os.environ.get('ANTIKYTHERA_REVIEW_ENABLED','1')=='1' if review_enabled is None else review_enabled
    app=FastAPI(title='Antikythera',version='1.0.0',description='Source-grounded research workspace. Human audits remain distinct from model proposals.')
    app.state.repository=repository;app.state.root=root
    executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='antikythera-rebuild')
    job_lock=threading.Lock()

    def read(path,default=None):
        if path.exists():return json.loads(path.read_text())
        if default is not None:return default
        raise HTTPException(503,'Run make report to generate the project data.')
    def writable(request):
        if not enabled:raise HTTPException(403,'Review writing is disabled for this service.')
        host=request.url.hostname
        # Reject browser requests from other sites, including DNS-rebinding hosts.
        allowed={'localhost','127.0.0.1','::1','testserver'}
        if host not in allowed:raise HTTPException(403,'Reviews are available only on the local workspace.')
        origin=request.headers.get('origin')
        if origin and urlparse(origin).hostname not in allowed:raise HTTPException(403,'A review must originate from the local workspace.')
    def record(kind,id_):
        try:return repository.get(kind,id_)
        except NotFound as exc:raise HTTPException(404,str(exc))
    @app.exception_handler(Conflict)
    async def conflict_handler(request,exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409,content={'detail':str(exc)})

    @app.get('/api/health')
    def health():return {'status':'ok','mode':'local','review_enabled':enabled,'scientific_validation':'pending'}
    @app.get('/api/catalog')
    def catalog():return read(root/'data/seed/catalog.json')
    @app.get('/api/workspace')
    def current_workspace():return workspace(root,repository,mode='local')
    @app.get('/api/report')
    def report():return read(root/'data/derived/report.json')
    @app.get('/api/records/{kind}')
    def records(kind:str,status:str|None=None,q:str='',limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0)):
        return {'records':repository.list(kind,status,q,limit,offset),'counts':repository.counts()}
    @app.get('/api/records/{kind}/{record_id}')
    def get_record(kind:str,record_id:str):return {'record':record(kind,record_id),'history':repository.history(kind,record_id)}
    @app.get('/api/evidence/{record_id}')
    def evidence(record_id:str):
        row=record('evidence',record_id)
        try:
            path=checked_path(root,row['record_path']);data=json.loads(path.read_text())
            import hashlib
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['record_sha256']:raise ValueError('Evidence file hash mismatch')
        except (KeyError,OSError,ValueError):raise HTTPException(409,'Retrieved evidence file is unavailable or has changed. Re-collect it before review.')
        return {'record':row,'abstract':data.get('abstract',''),'publication_types':data.get('publication_types',[]),'source_url':row.get('source_url')}
    @app.post('/api/reviews/{kind}/{record_id}')
    def review(kind:str,record_id:str,body:ReviewRequest,request:Request):
        writable(request);row=record(kind,record_id)
        try:
            fields=validate_review(kind,row,body.fields,root,body.decision)
            return repository.review(kind,record_id,body.reviewer,body.decision,body.note,body.expected_revision,fields,body.attested)
        except Conflict:raise
        except (ValueError,KeyError,OSError) as exc:raise HTTPException(422,str(exc))
    @app.post('/api/proposals/{kind}',status_code=201)
    def propose(kind:str,body:ProposalRequest,request:Request):
        writable(request)
        if kind not in ('identity','taxon'):raise HTTPException(422,'Only expert identity and taxon drafts can be added here.')
        allowed={'identity':{'plant_name_as_written','source_url','available_year','candidates','calibration_note'},'taxon':{'species_id','family','backbone_version','source_url','regions','hazard_trail'}}[kind]
        if set(body.payload)-allowed:raise HTTPException(422,'Unsupported proposal fields.')
        try:
            repository.get(kind,body.id)
            raise HTTPException(409,'This proposal ID already exists. Review its current revision instead.')
        except NotFound:pass
        if kind=='identity' and not isinstance(body.payload.get('candidates'),list):raise HTTPException(422,'Candidate rows are required.')
        repository.sync(kind,[{'id':body.id,**body.payload,'method':'expert_draft','status':'pending_review'}])
        return {'record':repository.get(kind,body.id)}
    @app.get('/api/reviews')
    def reviews():return {'events':repository.history(),'chain_valid':repository.verify_trail()}
    @app.post('/api/audits/{kind}/{record_id}')
    def audit(kind:str,record_id:str,body:AuditRequest,request:Request):
        writable(request)
        if not body.attested or not body.independent:raise HTTPException(422,'Independent human gold annotation must be explicitly attested.')
        row=record(kind,record_id)
        task={'claim':'extraction','evidence':'abstracts','identity':'identity','harmonisation':'harmonisation'}.get(kind)
        if not task:raise HTTPException(422,'This record does not have an audit task.')
        proposed=repository.proposal(kind,record_id)
        if kind=='evidence' and not proposed.get('verdict') and not proposed.get('offline_suggestion',{}).get('abstain',True):proposed={**proposed,**proposed['offline_suggestion']}
        prediction={k:proposed.get(k) for k in ('category','verdict','evidence_tier')}
        if task=='identity':
            candidates=proposed.get('candidates') or []
            eligible=[c for c in candidates if isinstance(c.get('probability'),(int,float))]
            if eligible:
                top=max(eligible,key=lambda c:c['probability']);prediction={'species_id':top.get('species_id'),'probability':top['probability']}
        from storage.repository import now
        entry={'kind':kind,'task':task,'item_id':record_id,'reviewer':body.reviewer.strip(),'attested':True,'independent':True,'gold':body.gold,'prediction':prediction,'note':body.note,'reviewed_at':now(),'proposal_hash':row['proposal_hash']}
        from audit.scoring import score
        entries=repository.valid_audits()
        try:metrics=score(entries+[entry])
        except ValueError as exc:raise HTTPException(422,str(exc))
        repository.add_audit(entry)
        return {'audit':entry,'metrics':metrics}
    @app.get('/api/audits')
    def audits():
        from audit.scoring import score
        entries=repository.valid_audits()
        return {'entries':entries,'metrics':score(entries),'invalidated':len(repository.metadata('audits',[]))-len(entries)}
    @app.get('/api/analysis')
    def analysis(freeze:int=Query(2000,ge=60,le=2026),follow_up:int=Query(20,ge=1,le=100),category:str|None=None):
        return analyze(read(root/'data/derived/dataset.json'),freeze_year=freeze,follow_up=follow_up,category=category,seed=1729)
    @app.get('/api/plants/{plant_id}')
    def plant(plant_id:str):
        found=next((p for p in catalog()['plants'] if p['id']==plant_id),None)
        if found is None:raise HTTPException(404,'Unknown plant')
        return found
    def rebuild_job(id_):
        if not job_lock.acquire(blocking=False):repository.update_job(id_,'failed',{'error':'Another rebuild is running.'});return
        try:
            repository.update_job(id_,'running')
            from scripts.pipeline import run
            result=run(root=root,collect=False)
            repository.update_job(id_,'succeeded',result)
        except Exception as exc:repository.update_job(id_,'failed',{'error':str(exc)})
        finally:job_lock.release()
    @app.post('/api/rebuild',status_code=202)
    def rebuild(request:Request):
        writable(request)
        id_=repository.job('offline_rebuild');executor.submit(rebuild_job,id_)
        return {'job_id':id_,'status':'queued','poll_url':'/api/jobs/'+id_}
    @app.get('/api/jobs/{job_id}')
    def job(job_id:str):
        try:return repository.get_job(job_id)
        except NotFound as exc:raise HTTPException(404,str(exc))
    if (root/'app/web/dist').exists():app.mount('/',StaticFiles(directory=root/'app/web/dist',html=True),name='workspace')
    return app

app=create_app()
