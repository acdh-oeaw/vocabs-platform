#!/usr/bin/env python3
"""Safety checks for operator-generated import and validation manifests."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/operator-plan.py"
class OperatorPlan(unittest.TestCase):
    def prepare(self, output, *extra):
        values = output.parent / "values.yaml"
        values.write_text(yaml.safe_dump({
            "data": {"activeClaim": "vocabs-data-r006", "revision": "r006",
                     "managedClaims": [{"name": "vocabs-data-r006", "size": "40Gi",
                                        "accessModes": ["ReadWriteMany"], "retain": True}]},
            "imports": {"job": {"enabled": False}},
            "fuseki": {"replicas": 1},
            "vinyl": {"podAnnotations": {"vocabs.acdh.oeaw.ac.at/data-revision": "vocabs-data-r006/r006"}},
            "ingress": {"enabled": True},
            "swagger": {"ingress": {"enabled": True}},
            "skosmos": {"config": {"existingConfigMap": "old-config", "revision": "r006"}},
        }))
        return subprocess.run([
            sys.executable, str(SCRIPT), "prepare", "--values", str(values),
            "--revision", "r007", "--claim", "vocabs-data-r007",
            "--source-claim", "vocabs-import", "--source", "/data/full-r006.nq",
            "--source", "/data/new.trig", "--job-name", "candidate-r007",
            "--output", str(output), *extra,
        ], text=True, capture_output=True)

    def test_cumulative_candidate_preserves_active_until_switch(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "r007"
            result = self.prepare(output, "--complete-source-set", "--config-map", "new-config", "--config-revision", "r007")
            self.assertEqual(result.returncode, 0, result.stderr)
            files = {p.name: yaml.safe_load(p.read_text()) for p in output.glob("*.yaml")}
            candidate = files["01-candidate-values.yaml"]
            self.assertEqual(candidate["data"]["activeClaim"], "vocabs-data-r006")
            self.assertEqual({c["name"] for c in candidate["data"]["managedClaims"]},
                             {"vocabs-data-r006", "vocabs-data-r007"})
            self.assertFalse(candidate["imports"]["job"]["enabled"])
            overlay = files["02-import-overlay.yaml"]["imports"]
            self.assertEqual(overlay["source"]["pvc"]["files"], ["/data/full-r006.nq", "/data/new.trig"])
            self.assertEqual(overlay["targetClaim"], "vocabs-data-r007")
            self.assertFalse(files["03-pause-values.yaml"]["ingress"]["enabled"])
            self.assertFalse(files["04-switch-values.yaml"]["swagger"]["ingress"]["enabled"])
            activated = files["05-active-values.yaml"]
            self.assertEqual(activated["data"]["activeClaim"], "vocabs-data-r007")
            self.assertEqual(activated["vinyl"]["podAnnotations"]["vocabs.acdh.oeaw.ac.at/data-revision"],
                             "vocabs-data-r007/r007")
            self.assertEqual(activated["skosmos"]["config"]["existingConfigMap"], "new-config")
            self.assertTrue(activated["ingress"]["enabled"])
            self.assertEqual(files["staging-pod.yaml"]["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"], "vocabs-import")

    def test_refuses_incomplete_or_reused_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "r007"
            result = self.prepare(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            result = self.prepare(output, "--complete-source-set")
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.prepare(output, "--complete-source-set")
            self.assertNotEqual(result.returncode, 0)

    def test_validator_does_not_join_active_service(self):
        fixture = {
            "kind": "StatefulSet", "spec": {
                "template": {
                    "metadata": {"labels": {"app.kubernetes.io/component": "fuseki", "app.kubernetes.io/instance": "vocabs-platform-dev"}},
                    "spec": {"containers": [{"name": "fuseki", "image": "fuseki:test"}],
                             "volumes": [{"name": "database", "persistentVolumeClaim": {"claimName": "vocabs-data-r006"}}]},
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "statefulset.yaml"
            output = Path(tmp) / "validator.yaml"
            source.write_text(yaml.safe_dump(fixture))
            result = subprocess.run([
                sys.executable, str(SCRIPT), "validator", "--rendered", str(source),
                "--claim", "vocabs-data-r007", "--name", "candidate-validator-r007",
                "--output", str(output),
            ], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            pod = yaml.safe_load(output.read_text())
            self.assertEqual(pod["metadata"]["labels"]["app.kubernetes.io/component"], "candidate-validator")
            self.assertEqual(pod["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"], "vocabs-data-r007")
            self.assertEqual(pod["spec"]["containers"][0]["image"], "fuseki:test")


if __name__ == "__main__":
    unittest.main()
