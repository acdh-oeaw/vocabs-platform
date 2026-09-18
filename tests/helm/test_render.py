#!/usr/bin/env python3
"""Cluster-free assertions on real rendered manifests, including negative cases."""
import copy, subprocess, tempfile, unittest
from pathlib import Path
import yaml
CHART = 'chart/vocabs'
class UniqueLoader(yaml.SafeLoader):
    pass
def unique_mapping(loader, node, deep=False):
    result = {}
    for key, value in node.value:
        key = loader.construct_object(key, deep=deep)
        if key in result:
            raise ValueError(f'duplicate YAML key: {key}')
        result[key] = loader.construct_object(value, deep=deep)
    return result
UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
def render(values=None, release='vocabs', namespace='test-a', fail=None):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
        yaml.safe_dump(values or {}, f); f.flush()
        p = subprocess.run(['helm', 'template', release, CHART, '--namespace', namespace, '-f', f.name], capture_output=True, text=True)
    if fail:
        assert p.returncode != 0, 'expected render failure'
        assert fail in p.stderr, p.stderr
        return
    assert p.returncode == 0, p.stderr
    return [d for d in yaml.load_all(p.stdout, Loader=UniqueLoader) if d]
def find(docs, kind, suffix=''):
    return next(d for d in docs if d['kind'] == kind and d['metadata']['name'].endswith(suffix))
def candidate():
    return {'imports': {'job': {'enabled': True}, 'targetClaim': 'candidate', 'source': {'pvc': {'existingClaim': 'source'}}}}
class Rendering(unittest.TestCase):
    def test_default_topology(self):
        docs = render()
        self.assertFalse(any(d['kind'] in ['Job', 'Ingress'] for d in docs))
        sts = find(docs, 'StatefulSet')
        self.assertEqual(sts['spec']['replicas'], 1)
        self.assertEqual(sts['spec']['podManagementPolicy'], 'OrderedReady')
        self.assertNotIn('volumeClaimTemplates', sts['spec'])
        self.assertEqual(sts['spec']['template']['spec']['volumes'][1]['persistentVolumeClaim']['claimName'], 'vocabs-data-r001')
        for d in docs:
            if d['kind'] == 'Service': self.assertEqual(d['spec']['type'], 'ClusterIP')
            if d['kind'] == 'PersistentVolumeClaim': self.assertEqual(d['metadata']['annotations']['helm.sh/resource-policy'], 'keep')
        self.assertIn('http://vocabs-varnish:80/skosmos/sparql', find(docs, 'ConfigMap', 'skosmos-config')['data']['config.ttl'])
        self.assertIn('.host = "vocabs-vocabs-fuseki"', find(docs, 'ConfigMap', 'vcl')['data']['default.vcl'])
        # Every policy peer must select a real workload in this release.
        pods = [d['spec']['template']['metadata']['labels'] for d in docs if d['kind'] in ['Deployment', 'StatefulSet']]
        for d in docs:
            if d['kind'] != 'NetworkPolicy': continue
            selectors = [d['spec']['podSelector']['matchLabels'], d['spec']['ingress'][0]['from'][0]['podSelector']['matchLabels']]
            for selector in selectors:
                self.assertTrue(any(all(p.get(k) == v for k,v in selector.items()) for p in pods), selector)
    def test_varnish_service_internal_only(self):
        docs = render()
        varnish = find(docs, 'Service', 'varnish')
        self.assertEqual(varnish['spec']['type'], 'ClusterIP')
        self.assertNotIn('externalTrafficPolicy', varnish['spec'])
        self.assertEqual(varnish['spec'].get('internalTrafficPolicy'), 'Cluster')
        self.assertEqual(varnish['spec']['ports'][0]['port'], 80)

    def test_skosmos_profile_uses_real_upstream_tag(self):
        profile = yaml.safe_load(Path('chart/vocabs/compatibility.yaml').read_text())['profiles']['2026.09.0-dev']
        self.assertEqual(profile['skosmos']['version'], '3.3')
        self.assertEqual(profile['skosmos']['upstreamTag'], 'v3.3')
        self.assertEqual(f"ghcr.io/acdh-oeaw/vocabs-skosmos:{profile['skosmos']['version']}-{profile['imageRevision']}", 'ghcr.io/acdh-oeaw/vocabs-skosmos:3.3-r1')

    def test_example_and_swagger_ingress(self):
        v = yaml.safe_load(Path('environments/example.yaml').read_text())
        v['swagger'] = {'enabled':True, 'specUrl':'https://vocabs.example.org/swagger.json', 'ingress':{'enabled':True, 'host':'api.example.org','allowAnubisBypass':True}}
        docs = render(v)
        ingress = [d for d in docs if d['kind']=='Ingress']
        self.assertEqual(len(ingress), 2)
        for i in ingress:
            backend=i['spec']['rules'][0]['http']['paths'][0]['backend']['service']['name']
            self.assertTrue(backend.endswith(('-gateway','-swagger')))

    def test_development_public_and_private_ingresses(self):
        values = yaml.safe_load(Path('environments/vocabs-platform-dev.yaml').read_text())
        docs = render(values, release='vocabs-platform-dev', namespace='vocabs-platform-dev')
        ingresses = {d['metadata']['name']: d for d in docs if d['kind'] == 'Ingress'}

        public = ingresses['vocabs-platform-dev-vocabs-gateway']
        self.assertEqual(public['spec']['ingressClassName'], 'nginx')
        self.assertEqual(public['spec']['rules'][0]['host'], 'vocabs-platform-dev.acdh-dev.oeaw.ac.at')
        self.assertEqual(public['spec']['tls'][0]['secretName'], 'vocabs-platform-dev-tls')
        self.assertEqual(public['metadata']['annotations']['cert-manager.io/cluster-issuer'], 'acdh-prod')
        self.assertTrue(public['spec']['rules'][0]['http']['paths'][0]['backend']['service']['name'].endswith('-gateway'))

        expected_private = '10.4.24.0/24,10.4.245.0/24'
        fuseki = ingresses['vocabs-platform-dev-vocabs-fuseki-admin']
        self.assertEqual(fuseki['spec']['ingressClassName'], 'nginx')
        self.assertEqual(fuseki['spec']['rules'][0]['host'], 'jena-vp-dev.acdh-dev.oeaw.ac.at')
        self.assertEqual(fuseki['spec']['tls'][0]['secretName'], 'jena-vp-dev-tls')
        self.assertEqual(fuseki['metadata']['annotations']['cert-manager.io/cluster-issuer'], 'acdh-prod')
        self.assertEqual(fuseki['metadata']['annotations']['nginx.ingress.kubernetes.io/whitelist-source-range'], expected_private)
        self.assertEqual(fuseki['spec']['rules'][0]['http']['paths'][0]['backend']['service']['name'], 'vocabs-platform-dev-vocabs-fuseki')

        swagger = ingresses['vocabs-platform-dev-vocabs-vocabsapi']
        self.assertEqual(swagger['spec']['ingressClassName'], 'nginx')
        self.assertEqual(swagger['spec']['rules'][0]['host'], 'vocabsapi-vp-dev.acdh-dev.oeaw.ac.at')
        self.assertEqual(swagger['spec']['tls'][0]['secretName'], 'vocabsapi-vp-dev-tls')
        self.assertEqual(swagger['metadata']['annotations']['cert-manager.io/cluster-issuer'], 'acdh-prod')
        self.assertEqual(swagger['metadata']['annotations']['nginx.ingress.kubernetes.io/whitelist-source-range'], expected_private)
        self.assertEqual(swagger['spec']['rules'][0]['http']['paths'][0]['backend']['service']['name'], 'vocabs-platform-dev-vocabs-swagger')
        self.assertEqual(find(docs, 'Service', 'fuseki')['spec']['type'], 'ClusterIP')
        self.assertEqual(find(docs, 'Service', 'swagger')['spec']['type'], 'ClusterIP')

    def test_private_ingresses_disabled_by_default(self):
        docs = render()
        self.assertFalse(any(d['kind'] == 'Ingress' for d in docs))
        self.assertNotIn('0.0.0.0/0', str(docs))
    def test_candidate_import(self):
        docs = render(candidate()); job = find(docs, 'Job')
        pod = job['spec']['template']['spec']
        self.assertEqual(pod['restartPolicy'], 'Never')
        self.assertEqual(pod['volumes'][0]['persistentVolumeClaim']['claimName'], 'candidate')
        self.assertEqual(pod['volumes'][1]['persistentVolumeClaim']['claimName'], 'source')
        self.assertTrue(pod['volumes'][1]['persistentVolumeClaim']['readOnly'])
        self.assertNotIn('helm.sh/hook', job['metadata'].get('annotations') or {})
        runtime=find(docs,'StatefulSet')['spec']['template']['spec']['containers'][0]['image']
        self.assertEqual(runtime.split(':')[-1], pod['containers'][0]['image'].split(':')[-1])
    def test_rejections(self):
        cases = [
          ({'stack':{'version':'unknown'}},'Unknown stack profile'),
          ({'fuseki':{'replicas':2}},'replicas'),
          ({'fuseki':{'service':{'type':'LoadBalancer'}}},'ClusterIP'),
          ({'varnish':{'server':{'service':{'type':'NodePort'}}}},'Varnish must remain internal'),
          ({'varnish':{'server':{'ingress':{'enabled':True}}}},'Varnish must remain internal'),
          ({'compatibility':{'overrides':{'jenaVersion':'5.5.0'}}},'allowUnsupported'),
          ({'fuseki':{'image':{'tag':'latest'}}},'tag'),
          ({'data':{'activeClaim':'other'}},'data-revision'),
          ({'data':{'managedClaims':[{'name':'data','size':'10Gi','accessModes':['ReadWriteOnce'],'retain':False}]}},'retain'),
          ({'imports':{'source':{'type':'url'}}},'pvc'),
        ]
        for values, message in cases:
            with self.subTest(values=values): render(values, fail=message)
        v=candidate(); v['imports']['targetClaim']='vocabs-data-r001'
        render(v, fail='Offline import into the active Fuseki database PVC is prohibited')
        v=candidate(); v['imports']['source']['pvc']['existingClaim']='vocabs-data-r001'
        render(v, fail='Import source must be separate')
    def test_tdb2_testing_override(self):
        v=candidate(); v['compatibility']={'allowUnsupported':True,'overrides':{'jenaVersion':'5.5.0','storageEngine':'TDB2'}}
        docs=render(v)
        self.assertIn('tdb2:DatasetTDB2',find(docs,'ConfigMap','fuseki-config')['data']['assembler.ttl'])
        for kind in ['StatefulSet','Job']:
            self.assertIn(':5.5.0-r1',find(docs,kind)['spec']['template']['spec']['containers'][0]['image'])
    def test_activation_and_namespaces(self):
        old=render(); v=yaml.safe_load(Path('chart/vocabs/examples/activate-r002.yaml').read_text()); new=render(v)
        def revision(docs):return find(docs,'Deployment','varnish')['spec']['template']['metadata']['annotations']['vocabs.acdh.oeaw.ac.at/data-revision']
        self.assertNotEqual(revision(old),revision(new))
        for release,namespace in [('vocab-a','namespace-a'),('vocab-b','namespace-b')]:
            docs=render(release=release,namespace=namespace)
            self.assertIn(f'.host = "{release}-vocabs-fuseki"',find(docs,'ConfigMap','vcl')['data']['default.vcl'])
    def test_config_checksum(self):
        docs=render({'skosmos':{'config':{'inline':'# changed'}}})
        a=find(render(),'Deployment','skosmos')['spec']['template']['metadata']['annotations']['checksum/config']
        b=find(docs,'Deployment','skosmos')['spec']['template']['metadata']['annotations']['checksum/config']
        self.assertNotEqual(a,b)
if __name__=='__main__': unittest.main()
