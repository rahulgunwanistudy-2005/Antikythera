"""Opt-in, provider-neutral structured inference adapter.

A configured endpoint accepts JSON {task,prompt,input,schema,model} and
returns {output: <structured JSON>}. Supply a gateway to adapt a vendor's
API. No paid model request occurs in collect or offline mode.
"""
import hashlib,json,os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen

class StructuredProvider:
    def __init__(self,endpoint=None,model=None,token=None,protocol=None):
        self.endpoint=endpoint or os.environ.get('ANTIKYTHERA_MODEL_ENDPOINT','')
        self.model=model or os.environ.get('ANTIKYTHERA_MODEL_NAME','')
        self.token=token if token is not None else os.environ.get('ANTIKYTHERA_MODEL_TOKEN','')
        self.protocol=protocol or os.environ.get('ANTIKYTHERA_MODEL_PROTOCOL','gateway')
        if self.protocol not in ('gateway','ollama'):raise ValueError('Model protocol must be gateway or ollama')
        parsed=urlparse(self.endpoint)
        if parsed.scheme!='https' and not(parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1')): raise ValueError('Model endpoint must use HTTPS or local HTTP')
        if parsed.username or parsed.password or parsed.query:raise ValueError('Keep endpoint credentials in the token environment variable')
    def run(self,task,prompt,input_data,schema,cache):
        body={'task':task,'prompt':prompt,'input':input_data,'schema':schema,'model':self.model}
        digest=hashlib.sha256(json.dumps([self.endpoint,self.protocol,body],sort_keys=True).encode()).hexdigest()
        path=Path(cache)/(digest+'.json');path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():return json.loads(path.read_text())['output']
        headers={'Content-Type':'application/json'}
        if self.token:headers['Authorization']='Bearer '+self.token
        request_body=body
        if self.protocol=='ollama':
            if not self.model:raise ValueError('Ollama model name is required')
            request_body={'model':self.model,'stream':False,'format':schema,'messages':[{'role':'system','content':prompt},{'role':'user','content':json.dumps(input_data,ensure_ascii=False)}]}
        request=Request(self.endpoint,data=json.dumps(request_body).encode(),headers=headers)
        try:
            with urlopen(request,timeout=120) as response:result=json.load(response)
        except Exception:raise RuntimeError('Structured model request failed; inspect the provider securely') from None
        if self.protocol=='ollama':
            try:result={'output':json.loads(result['message']['content'])}
            except (KeyError,TypeError,json.JSONDecodeError):raise ValueError('Ollama response did not contain structured JSON') from None
        if 'output' not in result:raise ValueError('Provider response requires output field')
        serialised=json.dumps(result['output'],ensure_ascii=False)
        if self.token and self.token in serialised:raise ValueError('Provider output contained a credential')
        saved={'task':task,'model':self.model,'request_sha256':digest,'output':result['output'],'reviewed':False}
        path.write_text(json.dumps(saved,ensure_ascii=False));return result['output']
