#!/usr/bin/env python3
"""Prepare reviewable files for a cumulative vocabulary import; never contact a cluster."""

import argparse
import copy
import re
from pathlib import Path

import yaml


def fail(message):
    raise SystemExit(message)


def write_yaml(path, value):
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True))


def prepare(args):
    values = yaml.safe_load(Path(args.values).read_text())
    if not isinstance(values, dict):
        fail("The environment values must be a YAML mapping")
    if not re.fullmatch(r"r[0-9]{3,}", args.revision):
        fail("Revision must look like r007 (three or more digits)")
    if not re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", args.claim) or len(args.claim) > 63:
        fail("Candidate PVC name must be a Kubernetes DNS label")
    if not re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", args.job_name) or len(args.job_name) > 40:
        fail("Job name must be a short Kubernetes DNS label")
    if not args.complete_source_set:
        fail("Pass --complete-source-set only after listing the RDF for ALL accepted vocabularies")
    if not args.source or len(set(args.source)) != len(args.source):
        fail("Provide one or more distinct --source /data/FILE arguments")
    if any(not re.fullmatch(r"/data/[A-Za-z0-9][A-Za-z0-9._/-]*", path)
           or ".." in Path(path).parts for path in args.source):
        fail("Source files must be safe absolute paths inside /data")
    if args.config_map and not args.config_revision:
        fail("--config-map also requires --config-revision")
    if args.config_revision and not args.config_map:
        fail("--config-revision also requires --config-map")
    if args.config_map and not re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", args.config_map):
        fail("ConfigMap name must be a Kubernetes DNS label")

    active = values["data"]["activeClaim"]
    current_revision = values["data"]["revision"]
    if args.claim == active or args.revision == current_revision:
        fail("Candidate claim/revision must differ from the active database")
    if values.get("imports", {}).get("job", {}).get("enabled", False):
        fail("Normal environment values must have imports.job.enabled=false")
    if values["vinyl"]["podAnnotations"]["vocabs.acdh.oeaw.ac.at/data-revision"] != f"{active}/{current_revision}":
        fail("Existing Vinyl revision does not match the active claim and revision")
    if values.get("fuseki", {}).get("replicas", 1) != 1:
        fail("Fuseki must have exactly one replica")
    claims = values["data"].get("managedClaims", [])
    if any(item["name"] == args.claim for item in claims):
        fail("Candidate claim already exists in managedClaims; use a fresh revision")
    if args.source_claim in {active, args.claim}:
        fail("RDF source PVC must differ from both database PVCs")
    before = copy.deepcopy(values)
    active_spec = next((item for item in claims if item["name"] == active), None)
    if not active_spec:
        fail("Active PVC is not managed in values; ask a maintainer for the candidate StorageClass")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    candidate_spec = copy.deepcopy(active_spec)
    candidate_spec["name"] = args.claim
    candidate_spec["retain"] = True
    if args.size:
        candidate_spec["size"] = args.size
    before["data"]["managedClaims"].append(candidate_spec)
    before.setdefault("imports", {}).setdefault("job", {})["enabled"] = False
    write_yaml(output / "01-candidate-values.yaml", before)

    import_overlay = {
        "imports": {
            "job": {"enabled": True, "name": args.job_name, "backoffLimit": 0},
            "targetClaim": args.claim,
            "source": {"type": "pvc", "pvc": {"existingClaim": args.source_claim, "files": args.source}},
        }
    }
    write_yaml(output / "02-import-overlay.yaml", import_overlay)

    pause = copy.deepcopy(before)
    pause["ingress"]["enabled"] = False
    pause["swagger"]["ingress"]["enabled"] = False
    write_yaml(output / "03-pause-values.yaml", pause)

    active_values = copy.deepcopy(before)
    active_values["data"]["activeClaim"] = args.claim
    active_values["data"]["revision"] = args.revision
    active_values["vinyl"]["podAnnotations"]["vocabs.acdh.oeaw.ac.at/data-revision"] = f"{args.claim}/{args.revision}"
    if args.config_map:
        active_values["skosmos"]["config"]["existingConfigMap"] = args.config_map
        active_values["skosmos"]["config"]["revision"] = args.config_revision
    switch = copy.deepcopy(active_values)
    switch["ingress"]["enabled"] = False
    switch["swagger"]["ingress"]["enabled"] = False
    write_yaml(output / "04-switch-values.yaml", switch)
    write_yaml(output / "05-active-values.yaml", active_values)

    pod = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": f"rdf-stage-{args.revision}", "labels": {"app.kubernetes.io/component": "rdf-staging"}},
        "spec": {
            "restartPolicy": "Never",
            "containers": [{
                "name": "stage", "image": "docker.io/library/busybox:1.36.1",
                "command": ["sh", "-c", "sleep 86400"],
                "volumeMounts": [{"name": "source", "mountPath": "/data"}],
            }],
            "volumes": [{"name": "source", "persistentVolumeClaim": {"claimName": args.source_claim}}],
        },
    }
    write_yaml(output / "staging-pod.yaml", pod)
    print(f"Plan: {output} (active {active}/{current_revision} → candidate {args.claim}/{args.revision})")
    print("No Kubernetes resources were changed. Review the source list and every generated file.")


def validator(args):
    documents = [item for item in yaml.safe_load_all(Path(args.rendered).read_text()) if item]
    statefulsets = [item for item in documents if item.get("kind") == "StatefulSet"]
    if len(statefulsets) != 1:
        fail("Expected exactly one rendered Fuseki StatefulSet")
    pod_spec = copy.deepcopy(statefulsets[0]["spec"]["template"]["spec"])
    volumes = [item for item in pod_spec["volumes"] if item["name"] == "database"]
    if len(volumes) != 1:
        fail("Rendered Fuseki pod has no unique database volume")
    old_claim = volumes[0]["persistentVolumeClaim"]["claimName"]
    if old_claim == args.claim:
        fail("Validator must never mount the active database claim")
    volumes[0]["persistentVolumeClaim"]["claimName"] = args.claim
    labels = copy.deepcopy(statefulsets[0]["spec"]["template"]["metadata"]["labels"])
    labels["app.kubernetes.io/component"] = "candidate-validator"
    pod = {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {"name": args.name, "labels": labels},
        "spec": pod_spec,
    }
    output = Path(args.output)
    if output.exists():
        fail("Validator manifest already exists; do not overwrite it")
    write_yaml(output, pod)
    print(f"Validator: {output} (candidate {args.claim}; active {old_claim} untouched)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare", help="Generate local candidate, import and activation values")
    p.add_argument("--values", required=True)
    p.add_argument("--revision", required=True)
    p.add_argument("--claim", required=True)
    p.add_argument("--source-claim", required=True)
    p.add_argument("--source", action="append", required=True)
    p.add_argument("--complete-source-set", action="store_true")
    p.add_argument("--size", help="Candidate PVC size; defaults to the active PVC size")
    p.add_argument("--job-name", required=True)
    p.add_argument("--config-map", help="Already created revisioned Skosmos ConfigMap")
    p.add_argument("--config-revision")
    p.add_argument("--output", required=True)
    p.set_defaults(func=prepare)
    v = commands.add_parser("validator", help="Generate isolated candidate Pod from rendered Fuseki StatefulSet")
    v.add_argument("--rendered", required=True)
    v.add_argument("--claim", required=True)
    v.add_argument("--name", required=True)
    v.add_argument("--output", required=True)
    v.set_defaults(func=validator)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
