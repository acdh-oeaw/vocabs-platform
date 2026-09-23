#!/usr/bin/env python3
"""Turtle syntax checks only; RIOT and real Jena integration remain separate."""
import subprocess
from pathlib import Path
import yaml
from rdflib import Dataset, Graph
for path in [*Path('config').rglob('*.ttl.example'), *Path('config').rglob('*.ttl'), *Path('tests/integration').glob('*.ttl')]:
    Graph().parse(path,format='turtle')
    print(f'Turtle syntax OK: {path}')
for path in Path('tests/integration').glob('*.trig'):
    Dataset().parse(path, format='trig')
    print(f'TriG syntax OK: {path}')
for override in [[], ['--set','compatibility.allowUnsupported=true','--set','compatibility.overrides.storageEngine=TDB2']]:
    result=subprocess.run(['helm','template','vocabs','chart/vocabs',*override],check=True,capture_output=True,text=True)
    for d in yaml.safe_load_all(result.stdout):
        if d and d['kind']=='ConfigMap':
            for key,value in d['data'].items():
                if key.endswith('.ttl'):Graph().parse(data=value,format='turtle')
print('Rendered TDB1/TDB2 assembler and Skosmos Turtle syntax OK (RDFLib, not RIOT)')
