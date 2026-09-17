#!/usr/bin/env python3
"""Validate external Skosmos TTL against environment values; optionally add a missing baseHref."""
import argparse
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
import yaml
from rdflib import Graph, Literal, Namespace, RDF

SKOSMOS = Namespace('http://purl.org/net/skosmos#')
def public_url(values):
    value = values.get('global', {}).get('publicUrl', '')
    if not re.fullmatch(r'https?://[a-z0-9]([a-z0-9.-]*[a-z0-9])?(:[0-9]{1,5})?/', value):
        raise ValueError('global.publicUrl must be an absolute http(s) root URL with trailing /')
    parsed = urlsplit(value)
    if len(parsed.hostname) > 253 or any(len(label)>63 or not re.fullmatch(r'[a-z0-9]([a-z0-9-]*[a-z0-9])?',label) for label in parsed.hostname.split('.')):
        raise ValueError('global.publicUrl has an invalid hostname')
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError('global.publicUrl has an invalid port')
    return value

def validate(config, expected, add_missing=False):
    graph = Graph().parse(data=config, format='turtle', publicID=expected)
    subjects = set(graph.subjects(RDF.type, SKOSMOS.Configuration))
    if len(subjects) != 1:
        raise ValueError('Expected exactly one skosmos:Configuration subject')
    subject = next(iter(subjects))
    bases = set(graph.objects(subject, SKOSMOS.baseHref))
    if not bases and add_missing:
        graph.add((subject, SKOSMOS.baseHref, Literal(expected)))
    elif bases != {Literal(expected)}:
        raise ValueError('Skosmos baseHref must be exactly the string in global.publicUrl; regenerate/review the external ConfigMap')
    return graph

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--values', required=True, help='Environment values containing global.publicUrl')
    parser.add_argument('--config', required=True, help='Combined config.ttl (or ConfigMap YAML with --configmap)')
    parser.add_argument('--configmap', action='store_true')
    parser.add_argument('--add-missing', action='store_true', help='Add a missing baseHref, writing validated Turtle to --config; conflicting values still fail')
    args = parser.parse_args()
    try:
        expected = public_url(yaml.safe_load(Path(args.values).read_text()))
        text = Path(args.config).read_text()
        if args.configmap:
            if args.add_missing: raise ValueError('--configmap is validation-only')
            text = yaml.safe_load(text)['data']['config.ttl']
        graph = validate(text, expected, args.add_missing)
        if args.add_missing:
            Path(args.config).write_text(graph.serialize(format='turtle'))
        print('Skosmos baseHref matches global.publicUrl', file=sys.stderr)
    except (ValueError, KeyError) as error:
        parser.exit(1, f'{error}\n')
