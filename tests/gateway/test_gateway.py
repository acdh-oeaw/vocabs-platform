#!/usr/bin/env python3
"""Gateway render and external Skosmos configuration contracts; no cluster required."""
import copy
import re
import importlib.util
from pathlib import Path
import sys
import unittest
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'helm'))
from test_render import render, find
spec=importlib.util.spec_from_file_location('skosmos_public_url', 'scripts/skosmos-public-url.py')
url_module=importlib.util.module_from_spec(spec); spec.loader.exec_module(url_module)
URL='https://vocabs.example.org/'
def values():return {'global':{'publicUrl':URL}, 'gateway':{'enabled':True,'anubis':{'signingKey':{'existingSecret':'test-anubis-signer'}}}, 'ingress':{'enabled':True}}
def config(docs):return find(docs,'ConfigMap','gateway-nginx')['data']['nginx.conf']
class Gateway(unittest.TestCase):
    def test_institute_naming(self):
        # Scan project text, excluding Git history and downloaded/generated artifacts.
        obsolete=re.compile(r'\bacdh[\s_\-\u2010-\u2015]*ch\b',re.I)
        root=Path(__file__).resolve().parents[2]
        findings=[]
        for path in root.rglob('*'):
            if not path.is_file() or any(part in {'.git','.venv','charts','__pycache__','node_modules','.build'} for part in path.relative_to(root).parts):continue
            try:text=path.read_text()
            except UnicodeDecodeError:continue
            for number,line in enumerate(text.splitlines(),1):
                if obsolete.search(line):findings.append(f'{path.relative_to(root)}:{number}')
        self.assertEqual(findings,[])
    def test_redirect_authority_with_port(self):
        v=values();v['global']['publicUrl']='https://vocabs.example.org:8443/'
        v['ingress']['tls']={'enabled':True,'secretName':'test-tls'}
        docs=render(v)
        pod=find(docs,'Deployment','gateway')['spec']['template']['spec']
        env={e['name']:e.get('value') for e in pod['containers'][0]['env']}
        self.assertEqual(env['REDIRECT_DOMAINS'],'vocabs.example.org:8443')
        ingress=find(docs,'Ingress')['spec']
        self.assertEqual(ingress['rules'][0]['host'],'vocabs.example.org')
        self.assertEqual(ingress['tls'][0]['hosts'],['vocabs.example.org'])
    def test_public_ingress_requires_signing_key(self):
        for missing in ['', '   ']:
            v=values();v['gateway']['anubis']['signingKey']['existingSecret']=missing
            render(v,fail='Public Ingress requires gateway.anubis.signingKey.existingSecret')
        v=values();v['gateway']['anubis']['signingKey']['existingSecret']=''
        v['compatibility']={'allowUnsupported':True}
        v['gateway']['anubis']['persistence']={'enabled':False}
        render(v,fail='Public Ingress requires gateway.anubis.signingKey.existingSecret')
        v['ingress']['enabled']=False
        render(v) # Explicitly non-public development still works without a key.
        render() # Generic/backend-only defaults still work.
        docs=render(values())
        pod=find(docs,'Deployment','gateway')['spec']['template']['spec']
        signer=next(e for e in pod['containers'][0]['env'] if e['name']=='ED25519_PRIVATE_KEY_HEX')
        self.assertEqual(signer['valueFrom']['secretKeyRef'],{'name':'test-anubis-signer','key':'ed25519-private-key-hex'})
    def test_public_path(self):
        docs=render(values()); svc=find(docs,'Service','gateway')
        self.assertEqual(svc['spec']['ports'],[{'name':'http','port':80,'targetPort':'anubis'}])
        ingress=find(docs,'Ingress')
        self.assertEqual(ingress['spec']['rules'][0]['host'],'vocabs.example.org')
        self.assertEqual(ingress['spec']['rules'][0]['http']['paths'][0]['backend']['service']['name'],svc['metadata']['name'])
        for i in [d for d in docs if d['kind']=='Ingress']:
            self.assertTrue(i['metadata']['name'].endswith('-gateway'))
        pod=find(docs,'Deployment','gateway')['spec']['template']['spec']
        self.assertEqual([c['name'] for c in pod['containers']],['anubis','nginx'])
        self.assertEqual(pod['containers'][0]['ports'],[{'name':'anubis','containerPort':8080}])
        self.assertNotIn('ports',pod['containers'][1])
        env={e['name']:e.get('value') for e in pod['containers'][0]['env']}
        self.assertEqual(env['TARGET'],'http://127.0.0.1:8081')
        self.assertEqual(env['PUBLIC_URL'],URL)
        for container in pod['containers']:
            self.assertIn('exec',container['readinessProbe'])
            self.assertTrue(container['securityContext']['runAsNonRoot'])
        self.assertIn('listen 127.0.0.1:8081;',config(docs))
        for kind in ['CustomResourceDefinition','ClusterRole','ClusterRoleBinding']:self.assertFalse(any(d['kind']==kind for d in docs))
    def test_url_validation(self):
        for url in ['', 'vocabs.example.org/', '/relative/', 'https://vocabs.example.org',
                    'https://vocabs.example.org/sub/', 'https://user:pw@vocabs.example.org/',
                    'https://vocabs.example.org/?q=x','https://vocabs.example.org/#frag',
                    'ftp://vocabs.example.org/','https://a..example.org/','https://vocabs.example.org:65536/']:
            v=values();v['global']['publicUrl']=url
            with self.subTest(url=url):render(v,fail='global.publicUrl')
        v=values();v['global']['publicUrl']='http://staging.example.org:8088/'
        docs=render(v);self.assertEqual(find(docs,'Ingress')['spec']['rules'][0]['host'],'staging.example.org')
        self.assertIn('proxy_set_header Host "staging.example.org:8088";',config(docs))
        render({'ingress':{'enabled':True},'global':{'publicUrl':URL}},fail='requires gateway')
        render({'ingress':{'host':'independent.example.org'}},fail='host')
    def test_redirects_headers_and_cors(self):
        docs=render(values());nginx=config(docs)
        names=yaml.safe_load(Path('chart/vocabs/values.yaml').read_text())['gateway']['conceptResolver']['namespaces']
        self.assertEqual(len(names),21)
        self.assertIn('|'.join(names),nginx)
        self.assertIn('set $vocabs_public_url "https://vocabs.example.org/"',nginx)
        for prefix in ['tadirah','invocation-type','bbt']:
            self.assertIn(f'location ~ ^/{prefix}(/|$)',nginx)
            self.assertIn(f'https://vocabs.dariah.eu/{prefix}',nginx)
        self.assertNotIn('vocabs.acdh.oeaw.ac.at',nginx)
        self.assertIn('map $http_x_forwarded_proto $public_scheme',nginx)
        self.assertIn('default https;',nginx)
        self.assertIn('X-Forwarded-Proto $public_scheme',nginx)
        self.assertNotIn('X-Forwarded-Proto $scheme',nginx)
        for header in ['Host','X-Forwarded-Host','X-Forwarded-For','X-Real-IP']:self.assertIn('proxy_set_header '+header,nginx)
        self.assertIn('"POST, GET, OPTIONS, DELETE, PUT" always;',nginx)
        self.assertIn('"x-requested-with, Content-Type, origin, accept" always;',nginx)
        self.assertIn('Access-Control-Max-Age "1000" always;',nginx)
        self.assertIn('if ($request_method = OPTIONS) { return 204; }',nginx)
        v=values();v['gateway']['cors']={'enabled':False}
        self.assertNotIn('Access-Control-',config(render(v)))
    def test_store_secrets_and_rollout(self):
        docs=render(values());deploy=find(docs,'Deployment','gateway')
        self.assertEqual(deploy['spec']['strategy'],{'type':'Recreate'})
        self.assertEqual(deploy['spec']['replicas'],1)
        pvc=find(docs,'PersistentVolumeClaim','gateway-state')
        self.assertEqual(pvc['metadata']['annotations']['helm.sh/resource-policy'],'keep')
        policy=yaml.safe_load(find(docs,'ConfigMap','gateway-anubis')['data']['policy.yaml'])
        self.assertEqual(policy['store'],{'backend':'bbolt','parameters':{'path':'/data/anubis.bdb'}})
        example=yaml.safe_load(Path('config/anubis/policy.yaml.example').read_text())
        self.assertEqual(policy,example)
        self.assertEqual(policy['bots'][0]['action'],'ALLOW')
        v=values();v['gateway']['anubis']={'persistence':{'enabled':False},'store':{'backend':'memory'},'policy':{'existingConfigMap':'reviewed-policy','revision':'r2'},'signingKey':{'existingSecret':'signer'}}
        docs=render(v);deploy=find(docs,'Deployment','gateway')
        self.assertFalse(any(d['kind']=='PersistentVolumeClaim' and d['metadata']['name'].endswith('gateway-state') for d in docs))
        self.assertFalse(any(d['kind']=='ConfigMap' and d['metadata']['name'].endswith('gateway-anubis') for d in docs))
        signer=next(e for e in deploy['spec']['template']['spec']['containers'][0]['env'] if e['name']=='ED25519_PRIVATE_KEY_HEX')
        self.assertEqual(signer['valueFrom']['secretKeyRef']['name'],'signer')
    def test_safety_rejections(self):
        patches=[({'replicas':2},'Gateway replicas must equal 1'),
          ({'anubis':{'enabled':False}},'requires Anubis'),
          ({'anubis':{'persistence':{'existingClaim':'vocabs-data-r001'}}},'separate from RDF'),
          ({'anubis':{'target':{'url':'http://outside:8081'}}},'127.0.0.1'),
          ({'anubis':{'image':{'tag':'latest'}}},'tag'),
          ({'nginx':{'image':{'tag':'stable'}}},'tag'),
          ({'nginx':{'listenPort':8082}},'8081'),
          ({'anubis':{'store':{'backend':'valkey'}}},'backend'),
          ({'anubis':{'store':{'backend':'memory'}}},'persistence requires'),
          ({'conceptResolver':{'namespaces':['bad|regex']}},'namespaces'),
          ({'externalRedirects':[{'prefix':'archecategory','targetBaseUrl':'https://example.net/foo','status':301}]},'conflicting'),
          ({'externalRedirects':[{'prefix':'a','targetBaseUrl':'https://example.net/";$host','status':301}]},'targetBaseUrl')]
        for patch,reason in patches:
            v=values();v['gateway'].update(patch)
            with self.subTest(patch=patch):render(v,fail=reason)
        render({'swagger':{'enabled':True,'specUrl':URL+'swagger.json','ingress':{'enabled':True,'host':'api.example.org'}}},fail='bypasses Anubis')
    def test_network_and_config(self):
        docs=render(values());policy=find(docs,'NetworkPolicy','gateway')
        self.assertEqual(policy['spec']['ingress'],[])
        v=values();v['networkPolicy']={'gatewayIngressPeers':[{'namespaceSelector':{'matchLabels':{'operator-supplied':'ingress'}},'podSelector':{'matchLabels':{'role':'ingress'}}}]}
        docs=render(v);rule=find(docs,'NetworkPolicy','gateway')['spec']['ingress'][0]
        self.assertEqual(rule['ports'],[{'protocol':'TCP','port':8080}])
        self.assertEqual(rule['from'],v['networkPolicy']['gatewayIngressPeers'])
        skosmos=find(docs,'NetworkPolicy','skosmos')
        self.assertEqual(skosmos['spec']['ingress'][0]['from'][0]['podSelector']['matchLabels']['app.kubernetes.io/component'],'gateway')
        ttl=find(docs,'ConfigMap','skosmos-config')['data']['config.ttl']
        url_module.validate(ttl,URL)
        v['global']['publicUrl']='https://new.example.org/'
        new=render(v)
        a=find(docs,'Deployment','gateway')['spec']['template']['metadata']['annotations']['checksum/nginx']
        b=find(new,'Deployment','gateway')['spec']['template']['metadata']['annotations']['checksum/nginx']
        self.assertNotEqual(a,b)
    def test_external_config_contract(self):
        config=Path('config/skosmos/base.ttl.example').read_text()
        with self.assertRaises(ValueError):url_module.validate(config,URL)
        graph=url_module.validate(config,URL,add_missing=True)
        serialized=graph.serialize(format='turtle')
        url_module.validate(serialized,URL)
        with self.assertRaises(ValueError):url_module.validate(serialized,'https://wrong.example.org/')
        with self.assertRaises(ValueError):url_module.validate(serialized,'https://wrong.example.org/',add_missing=True)
if __name__=='__main__':unittest.main()
