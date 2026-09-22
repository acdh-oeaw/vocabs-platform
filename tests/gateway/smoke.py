#!/usr/bin/env python3
"""Optional Podman smoke test: exact gateway images + a mock Skosmos HTTP backend.
Uses localhost ports 8080/8081/9090 and no cluster. Does NOT test actual Skosmos.
"""
from contextlib import closing
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import uuid
import yaml

ROOT=Path(__file__).resolve().parents[2]
def podman(*args, check=True):
    return subprocess.run(['podman',*map(str,args)],check=check,capture_output=True,text=True)
class MockSkosmos(BaseHTTPRequestHandler):
    def do_GET(self):
        body=json.dumps({'path':self.path,'headers':dict(self.headers)}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass

def request(method,path,headers=None):
    headers={'Host':'vocabs.example.org','X-Forwarded-Proto':'https','X-Forwarded-For':'198.51.100.10','X-Real-IP':'198.51.100.10',**(headers or {})}
    with closing(http.client.HTTPConnection('127.0.0.1',8080,timeout=5)) as conn:
        conn.request(method,path,headers=headers)
        response=conn.getresponse()
        return response.status,dict(response.getheaders()),response.read()

def main():
    for port in [8080,8081,9090]:
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            sock.bind(('127.0.0.1',port))
    mock=ThreadingHTTPServer(('127.0.0.1',0),MockSkosmos)
    thread=threading.Thread(target=mock.serve_forever,daemon=True);thread.start()
    names=[]
    try:
        with tempfile.TemporaryDirectory(prefix='vocabs-gateway-') as tmp:
            tmp=Path(tmp);tmp.chmod(0o755)
            config=tmp/'config';config.mkdir(mode=0o755)
            state=tmp/'state';state.mkdir(mode=0o777);state.chmod(0o777) # Disposable test state, mapped container UID.
            result=subprocess.check_output(['helm','template','vocabs',str(ROOT/'chart/vocabs'),
                '--set','global.publicUrl=https://vocabs.example.org/', '--set','gateway.enabled=true',
                '--set',f'skosmos.service.port={mock.server_port}'],text=True)
            manifests=list(yaml.safe_load_all(result))
            for d in manifests:
                if d and d['kind']=='ConfigMap' and '-gateway-' in d['metadata']['name']:
                    for key,value in d['data'].items():(config/key).write_text(value)
            deployment=next(d for d in manifests if d and d['kind']=='Deployment' and d['metadata']['name'].endswith('-gateway'))
            containers=deployment['spec']['template']['spec']['containers']
            nginx,anubis=containers[1],containers[0]
            run=['run','--rm','--network=host','--read-only','--cap-drop=all','--security-opt=no-new-privileges']
            nginx_options=['--tmpfs','/tmp:rw,mode=1777','--add-host','vocabs-vocabs-skosmos:127.0.0.1','-v',f'{config}:/etc/vocabs:ro','--entrypoint','nginx']
            checked=podman(*run,*nginx_options,nginx['image'],'-t','-c','/etc/vocabs/nginx.conf')
            print(checked.stderr.strip(),flush=True)
            nginx_name='vocabs-nginx-smoke-'+uuid.uuid4().hex[:8];names.append(nginx_name)
            podman(*run,'-d','--name',nginx_name,*nginx_options,nginx['image'],*nginx['args'])
            anubis_name='vocabs-anubis-smoke-'+uuid.uuid4().hex[:8];names.append(anubis_name)
            env=[]
            for entry in anubis['env']:
                # Limit the temporary host-network listener to localhost; the pod listens on :8080.
                value='127.0.0.1:8080' if entry['name']=='BIND' else entry['value']
                env+=['-e',entry['name']+'='+value]
            podman(*run,'-d','--name',anubis_name,'-v',f'{config}:/etc/anubis:ro','-v',f'{state}:/data:rw',*env,anubis['image'])
            for _ in range(60):
                health=podman('exec',anubis_name,'/ko-app/anubis','-healthcheck',check=False)
                if health.returncode==0:break
                time.sleep(0.25)
            else:raise RuntimeError('Anubis failed readiness')
            podman('exec',nginx_name,'wget','-q','-O','/dev/null','http://127.0.0.1:8081/healthz')
            for path in ['/concept-a/example','/concept-b/deu','/concept-a/a%2Fb?x=1&y=2']:
                status,headers,_=request('GET',path)
                from urllib.parse import urlsplit,parse_qs
                assert status==302,(status,headers)
                target=urlsplit(headers['Location'])
                assert target.path=='/entity'
                assert parse_qs(target.query)['uri']==['https://vocabs.example.org'+path]
            for prefix in ['external-vocab','other-vocab','third-vocab']:
                for suffix in ['', '/foo', '/a%2Fb?x=1']:
                    status,headers,_=request('GET','/'+prefix+suffix)
                    assert status==301,(status,headers)
                    assert headers['Location']=='https://vocabs.dariah.eu/'+prefix+suffix,headers
            for accept in ['text/turtle','application/rdf+xml','application/ld+json']:
                status,_,body=request('GET','/entity?uri=example',{'User-Agent':'Mozilla/5.0','Accept':accept})
                assert status==200,(status,body)
                upstream=json.loads(body)['headers']
                for key,value in {'Host':'vocabs.example.org','X-Forwarded-Host':'vocabs.example.org','X-Forwarded-Proto':'https','X-Real-IP':'198.51.100.10','X-Forwarded-For':'198.51.100.10'}.items():
                    assert upstream[key]==value,(key,upstream)
            assert request('GET','/rest/v1/vocabularies',{'User-Agent':'Mozilla/5.0','Accept':'text/html'})[0]==200
            for path in ['/rest/v1/vocabularies','/concept-a/example']:
                status,headers,_=request('OPTIONS',path)
                assert status==204,(status,headers)
                assert headers['Access-Control-Allow-Methods']=='POST, GET, OPTIONS, DELETE, PUT'
                assert headers['Access-Control-Allow-Headers']=='x-requested-with, Content-Type, origin, accept'
                assert headers['Access-Control-Max-Age']=='1000'
            status,headers,body=request('GET','/',{'User-Agent':'Mozilla/5.0','Accept':'text/html'})
            assert 'text/html' in headers.get('Content-Type',''),(status,headers,body)
            assert b'anubis' in body.lower(),body
            assert any(state.iterdir()),'bbolt did not create persistent state'
            print('PASS: nginx -t, both exec probes, concept/DARIAH redirects, forwarded HTTPS/client headers, CORS, API/RDF passthrough, browser challenge response and bbolt file creation.',flush=True)
            print('Scope: exact gateway images with a mock Skosmos backend; no real browser challenge solution or Kubernetes test.',flush=True)
    except Exception:
        for name in names:
            logs=podman('logs',name,check=False)
            print(name,logs.stdout,logs.stderr)
        raise
    finally:
        for name in reversed(names):podman('rm','-f',name,check=False)
        mock.shutdown();mock.server_close();thread.join()
if __name__=='__main__':main()
