#!/usr/bin/env python3
"""Build all local images; never push automatically."""
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
debian_base = 'docker.io/library/debian:bookworm-slim@sha256:f3034a6ec3c1205360777c4aae76234998866ad18806ae62b63a3f84ccad782b'

for component, image in [
    ('skosmos', 'vocabs-skosmos'),
    ('fuseki-runtime', 'vocabs-fuseki'),
    ('jena-tools', 'vocabs-jena-tools'),
    ('vinyl', 'vocabs-vinyl'),
]:
    if component == 'skosmos':
        v = s['skosmos']['version']
        revision = s['skosmos'].get('imageRevision', s['imageRevision'])
        tag = f'{a.registry}/{image}:{v}-{revision}'
    elif component == 'vinyl':
        v = s['vinyl']['version']
        tag = f'{a.registry}/{image}:{v}'
    else:
        v = s['jena']['version']
        revision = s['imageRevision']
        if component == 'jena-tools':
            revision = s['importer'].get('imageRevision', revision)
        tag = f'{a.registry}/{image}:{v}-{revision}'

    args = ['docker', 'build', '-f', f'images/{component}/Dockerfile', '-t', tag]

    if component == 'skosmos':
        args += [
            '--build-arg',
            f'SKOSMOS_UPSTREAM_TAG={s["skosmos"]["upstreamTag"]}',
        ]
    elif component == 'vinyl':
        args += [
            '--build-arg', f'DEBIAN_BASE_IMAGE={debian_base}',
            '--build-arg', f'VINYL_VERSION={v}',
            '--build-arg', f'VINYL_SHA256={s["vinyl"]["sha256"]}',
        ]
    else:
        checksum = s['jena']['fusekiSha512' if component == 'fuseki-runtime' else 'toolsSha512']
        args += [
            '--build-arg', f'JAVA_BASE_IMAGE={a.java_base}',
            '--build-arg', f'JENA_VERSION={v}',
            '--build-arg', f'JENA_SHA512={checksum}',
        ]
        if component == 'jena-tools':
            args += [
                '--build-arg',
                f'FUSEKI_SHA512={s["jena"]["fusekiSha512"]}',
            ]

    subprocess.run(args + ['.'], check=True)
