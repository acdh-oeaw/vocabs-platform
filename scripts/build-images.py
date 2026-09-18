#!/usr/bin/env python3
"""Build all three local images; never push automatically."""
import argparse, subprocess
from pathlib import Path
import yaml
p = argparse.ArgumentParser()
p.add_argument('--stack', default='2026.09.0-dev')
p.add_argument('--java-base', required=True, help='Debian/Ubuntu Java 21 JDK image pinned with @sha256:...')
p.add_argument('--registry', default='ghcr.io/acdh-oeaw')
a = p.parse_args()
if '@sha256:' not in a.java_base:
    p.error('--java-base must be pinned by digest')
profiles = yaml.safe_load(Path('chart/vocabs/compatibility.yaml').read_text())['profiles']
s = profiles[a.stack]
assert s['jena']['version'] == s['importer']['jenaVersion']
for component, image in [('skosmos', 'vocabs-skosmos'), ('fuseki-runtime', 'vocabs-fuseki'), ('jena-tools', 'vocabs-jena-tools')]:
    v = s['skosmos']['version'] if component == 'skosmos' else s['jena']['version']
    revision = s['skosmos'].get('imageRevision', s['imageRevision']) if component == 'skosmos' else s['imageRevision']
    args = ['docker', 'build', '-f', f'images/{component}/Dockerfile', '-t', f'{a.registry}/{image}:{v}-{revision}']
    if component == 'skosmos':
        args += ['--build-arg', f'SKOSMOS_UPSTREAM_TAG={s["skosmos"]["upstreamTag"]}']
    else:
        checksum = s['jena']['fusekiSha512' if component == 'fuseki-runtime' else 'toolsSha512']
        args += ['--build-arg', f'JAVA_BASE_IMAGE={a.java_base}', '--build-arg', f'JENA_VERSION={v}', '--build-arg', f'JENA_SHA512={checksum}']
        if component == 'jena-tools':
            args += ['--build-arg', f'FUSEKI_SHA512={s["jena"]["fusekiSha512"]}']
    subprocess.run(args + ['.'], check=True)
