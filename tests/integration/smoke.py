#!/usr/bin/env python3
"""Optional real Jena smoke test. Requires Java 21, extracted Jena/Fuseki and local TCP."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('--jena-home', type=Path, required=True)
parser.add_argument('--fuseki-jar', type=Path, required=True)
a = parser.parse_args()
a.jena_home = a.jena_home.resolve()
a.fuseki_jar = a.fuseki_jar.resolve()
root = Path(__file__).resolve().parents[2]
profile = yaml.safe_load((root/'chart/vocabs/compatibility.yaml').read_text())['profiles']['2026.09.0-dev']
version = profile['jena']['version']
for engine in ['TDB1', 'TDB2']:
    with tempfile.TemporaryDirectory(prefix='vocabs-jena-') as tmp:
        work = Path(tmp)
        flags = [] if engine == 'TDB1' else ['--set', 'compatibility.allowUnsupported=true', '--set', 'compatibility.overrides.storageEngine=TDB2']
        manifests = subprocess.check_output(['helm', 'template', 'vocabs', str(root/'chart/vocabs'), *flags], text=True)
        config = next(d['data']['assembler.ttl'] for d in yaml.safe_load_all(manifests) if d and d['kind']=='ConfigMap' and 'assembler.ttl' in d.get('data', {}))
        assembler = work/'assembler.ttl'
        assembler.write_text(config.replace('/fuseki/databases', str(work)))
        env = {**os.environ, 'PATH':str(a.jena_home/'bin')+':'+os.environ['PATH'],
               'JENA_HOME':str(a.jena_home), 'FUSEKI_JAR':str(a.fuseki_jar),
               'JENA_VERSION':version, 'EXPECTED_JENA_VERSION':version,
               'STORAGE_ENGINE':engine, 'ASSEMBLER':str(assembler),
               'TEXT_INDEX_DIR':str(work/'text'), 'BUILD_TEXT_INDEX':'true', 'VALIDATE_RDF':'true'}
        subprocess.run([str(root/'images/jena-tools/load.sh'), str(work/'db'), str(root/'tests/integration/vocabulary.ttl')], env=env, check=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        with (work/'server.log').open('w+') as log:
            server = subprocess.Popen(['java', '-jar', str(a.fuseki_jar), '--localhost', f'--port={port}', f'--config={assembler}'], cwd=work, stdout=log, stderr=subprocess.STDOUT)
            try:
                base = f'http://127.0.0.1:{port}'
                for attempt in range(60):
                    if server.poll() is not None:
                        raise RuntimeError('Fuseki exited before readiness')
                    try:
                        with urllib.request.urlopen(base+'/$/ping', timeout=1) as response:
                            if response.status == 200: break
                    except (OSError, urllib.error.URLError):
                        time.sleep(0.25)
                else: raise RuntimeError('Fuseki did not become ready')
                def query(sparql):
                    request = urllib.request.Request(base+'/skosmos/sparql?'+urllib.parse.urlencode({'query':sparql}), headers={'Accept':'application/sparql-results+json'})
                    with urllib.request.urlopen(request, timeout=10) as response:
                        return json.load(response)['results']['bindings']
                assert query('SELECT (COUNT(*) AS ?n) WHERE {?s ?p ?o}')[0]['n']['value']=='22'
                bindings=query('PREFIX text:<http://jena.apache.org/text#> SELECT ?s WHERE { ?s text:query "modern art" }')
                assert any(b['s']['value']=='https://example.org/concept/modernArt' for b in bindings), bindings
                print(f'{engine}: 22 triples, JenaText multi-word search and HTTP readiness passed', flush=True)
            except Exception:
                log.flush(); log.seek(0); print(log.read())
                raise
            finally:
                if server.poll() is None:
                    server.terminate() # SIGTERM, no database lock manipulation.
                    try: server.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        server.kill(); server.wait()
                        raise RuntimeError('Fuseki did not shut down gracefully within 30s')
            assert server.returncode in (0, 143, -15), server.returncode
            print(f'{engine}: SIGTERM shutdown passed', flush=True)
