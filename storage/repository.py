"""DuckDB repository with optimistic revisions and an append-only review trail.

Proposal imports never become human reviews. All SQL values are parameterized.
The database lives locally and is excluded from the public static export.
"""
from __future__ import annotations
import hashlib
import json
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import duckdb

LOCK=threading.RLock()
KINDS={'claim','evidence','identity','taxon','effort','harmonisation'}

def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()

class Conflict(ValueError):pass
class NotFound(ValueError):pass

class Repository:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records (kind VARCHAR, id VARCHAR, payload VARCHAR NOT NULL, proposal_hash VARCHAR NOT NULL, revision INTEGER NOT NULL, review_status VARCHAR NOT NULL, review_fields VARCHAR NOT NULL, reviewer VARCHAR, reviewed_at VARCHAR, PRIMARY KEY(kind,id))')
            db.execute('CREATE TABLE IF NOT EXISTS review_events (sequence BIGINT PRIMARY KEY, id VARCHAR UNIQUE, body VARCHAR NOT NULL, event_hash VARCHAR NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS jobs (id VARCHAR PRIMARY KEY, action VARCHAR, status VARCHAR, started_at VARCHAR, finished_at VARCHAR, result VARCHAR)')
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key VARCHAR PRIMARY KEY, value VARCHAR)')
    @contextmanager
    def connect(self):
        with LOCK:
            con=duckdb.connect(str(self.path))
            try:yield con
            finally:con.close()
    def _event(self,db,body):
        last=db.execute('SELECT sequence,event_hash FROM review_events ORDER BY sequence DESC LIMIT 1').fetchone()
        sequence=last[0]+1 if last else 1
        body={**body,'id':str(uuid.uuid4()),'sequence':sequence,'previous_hash':last[1] if last else None,'timestamp':now()}
        hash_=digest(body)
        db.execute('INSERT INTO review_events VALUES (?,?,?,?)',[sequence,body['id'],canonical(body),hash_])
        return {**body,'event_hash':hash_}
    @staticmethod
    def _row(row):
        if row is None:raise NotFound('Record not found')
        kind,id_,payload,hash_,revision,status,fields,reviewer,at=row
        return {**json.loads(payload),**json.loads(fields),'id':id_,'kind':kind,'proposal_hash':hash_,'revision':revision,'review_status':status,'reviewer':reviewer,'reviewed_at':at,'reviewed':status=='accept'}
    def sync(self,kind,records):
        if kind not in KINDS:raise ValueError('Unknown record kind')
        seen=set()
        for record in records:
            if not isinstance(record.get('id'),str) or not record['id'] or record['id'] in seen:raise ValueError('Unique nonempty proposal IDs required')
            seen.add(record['id'])
        inserted=changed=0
        with self.connect() as db:
            db.execute('BEGIN TRANSACTION')
            try:
                for record in records:
                    # Collector-owned flags cannot inject a review decision.
                    payload={k:v for k,v in record.items() if k not in ('reviewed','reviewer','reviewed_at','revision','review_status','proposal_hash')}
                    id_=payload['id'];hash_=digest(payload)
                    old=db.execute('SELECT proposal_hash,revision,review_status FROM records WHERE kind=? AND id=?',[kind,id_]).fetchone()
                    if old is None:
                        db.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?)',[kind,id_,canonical(payload),hash_,0,'pending','{}',None,None]);inserted+=1
                    elif old[0]!=hash_:
                        db.execute('UPDATE records SET payload=?, proposal_hash=?, revision=?, review_status=?, review_fields=?,reviewer=NULL,reviewed_at=NULL WHERE kind=? AND id=?',[canonical(payload),hash_,old[1]+1,'pending','{}',kind,id_]);changed+=1
                        self._event(db,{'type':'proposal_changed','kind':kind,'record_id':id_,'old_hash':old[0],'proposal_hash':hash_,'invalidated_status':old[2]})
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK');raise
        return {'inserted':inserted,'changed':changed,'total_imported':len(records)}
    def list(self,kind=None,status=None,query='',limit=10000,offset=0):
        clauses=[];params=[]
        if kind is not None:clauses.append('kind=?');params.append(kind)
        if status is not None:clauses.append('review_status=?');params.append(status)
        if query:clauses.append('lower(payload) LIKE ?');params.append('%'+query.lower()+'%')
        where=' WHERE '+' AND '.join(clauses) if clauses else ''
        with self.connect() as db:
            rows=db.execute('SELECT * FROM records'+where+' ORDER BY kind,id LIMIT ? OFFSET ?',params+[limit,offset]).fetchall()
        return [self._row(row) for row in rows]
    def get(self,kind,id_):
        with self.connect() as db:return self._row(db.execute('SELECT * FROM records WHERE kind=? AND id=?',[kind,id_]).fetchone())
    def proposal(self,kind,id_):
        with self.connect() as db:row=db.execute('SELECT payload FROM records WHERE kind=? AND id=?',[kind,id_]).fetchone()
        if row is None:raise NotFound('Record not found')
        return json.loads(row[0])
    def valid_audits(self):
        entries=self.metadata('audits',[]);valid=[]
        for entry in entries:
            try:current=self.get(entry['kind'],entry['item_id'])
            except (NotFound,KeyError):continue
            if current['proposal_hash']==entry.get('proposal_hash'):valid.append(entry)
        return valid
    def add_audit(self,entry):
        with self.connect() as db:
            db.execute('BEGIN TRANSACTION')
            try:
                row=db.execute('SELECT value FROM metadata WHERE key=?',['audits']).fetchone()
                entries=json.loads(row[0]) if row else []
                if any(e.get('task')==entry['task'] and e.get('item_id')==entry['item_id'] and e.get('proposal_hash')==entry['proposal_hash'] for e in entries):raise Conflict('An audit already exists for this proposal version. Adjudicate gold before replacing it.')
                event=self._event(db,{'type':'human_audit','kind':entry['kind'],'record_id':entry['item_id'],'reviewer':entry['reviewer'],'audit':entry})
                entries.append({**entry,'event_hash':event['event_hash']})
                db.execute('INSERT INTO metadata VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',['audits',canonical(entries)])
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK');raise
        return event
    def review(self,kind,id_,reviewer,decision,note,expected_revision,fields,attested=False):
        if kind not in KINDS or decision not in ('accept','reject','defer'):raise ValueError('Invalid review kind or decision')
        if attested is not True or not isinstance(reviewer,str) or len(reviewer.strip())<2:raise ValueError('An explicitly attested reviewer name is required')
        if not isinstance(note,str) or not note.strip():raise ValueError('A review note is required')
        if type(expected_revision) is not int or expected_revision<0:raise ValueError('Expected revision must be a nonnegative integer')
        if not isinstance(fields,dict):raise ValueError('Review fields must be an object')
        with self.connect() as db:
            db.execute('BEGIN TRANSACTION')
            try:
                old=self._row(db.execute('SELECT * FROM records WHERE kind=? AND id=?',[kind,id_]).fetchone())
                if old['revision']!=expected_revision:raise Conflict('This record changed. Reload it before reviewing.')
                revision=expected_revision+1
                event=self._event(db,{'type':'human_review','kind':kind,'record_id':id_,'proposal_hash':old['proposal_hash'],'reviewer':reviewer.strip(),'decision':decision,'note':note.strip(),'attested':True,'fields':fields,'revision':revision})
                db.execute('UPDATE records SET revision=?,review_status=?,review_fields=?,reviewer=?,reviewed_at=? WHERE kind=? AND id=?',[revision,decision,canonical(fields),reviewer.strip(),event['timestamp'],kind,id_])
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK');raise
        return {'record':self.get(kind,id_),'review':event,'revision':revision}
    def history(self,kind=None,id_=None):
        with self.connect() as db:rows=db.execute('SELECT body,event_hash FROM review_events ORDER BY sequence').fetchall()
        events=[{**json.loads(body),'event_hash':hash_} for body,hash_ in rows]
        return [e for e in events if (kind is None or e.get('kind')==kind) and (id_ is None or e.get('record_id')==id_)]
    def verify_trail(self):
        previous=None
        for event in self.history():
            body={k:v for k,v in event.items() if k!='event_hash'}
            if body.get('previous_hash')!=previous or digest(body)!=event['event_hash']:return False
            previous=event['event_hash']
        return True
    def counts(self):
        with self.connect() as db:rows=db.execute('SELECT kind,review_status,count(*) FROM records GROUP BY kind,review_status').fetchall()
        result={}
        for kind,status,n in rows:result.setdefault(kind,{})[status]=n
        return result
    def set_metadata(self,key,value):
        with self.connect() as db:db.execute('INSERT INTO metadata VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',[key,canonical(value)])
    def metadata(self,key,default=None):
        with self.connect() as db:row=db.execute('SELECT value FROM metadata WHERE key=?',[key]).fetchone()
        return json.loads(row[0]) if row else default
    def job(self,action):
        id_=str(uuid.uuid4())
        with self.connect() as db:db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?)',[id_,action,'queued',now(),None,'{}'])
        return id_
    def update_job(self,id_,status,result=None):
        with self.connect() as db:db.execute('UPDATE jobs SET status=?,finished_at=?,result=? WHERE id=?',[status,now() if status in ('succeeded','failed') else None,canonical(result or {}),id_])
    def get_job(self,id_):
        with self.connect() as db:row=db.execute('SELECT * FROM jobs WHERE id=?',[id_]).fetchone()
        if not row:raise NotFound('Job not found')
        return dict(zip(('id','action','status','started_at','finished_at','result'),row[:-1]+(json.loads(row[-1]),)))
    def export_parquet(self,directory):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            # File path is bound separately; the query/table is fixed.
            for kind in ('claim','evidence','identity','taxon','effort'):
                db.execute('COPY (SELECT * FROM records WHERE kind=$record_kind) TO $destination (FORMAT PARQUET)',{'record_kind':kind,'destination':str(directory/(kind+'s.parquet'))})
        return directory
