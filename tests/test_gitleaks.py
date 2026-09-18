"""Exercise the real scanner without committing or retaining test secrets."""
import json
import secrets
import subprocess
import tempfile
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / '.gitleaks.toml'
FIELD_NAME = 'ed25519' + '-private-key-hex'


def scan(path, value, expected):
    with tempfile.TemporaryDirectory(prefix='vocabs-gitleaks-test-') as directory:
        root = Path(directory)
        fixture = root / path
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(f'api_key = "{value}"\n')
        result = subprocess.run(
            ['gitleaks', 'dir', '--redact', '--config', str(CONFIG),
             '--report-format', 'json', '--report-path', str(root / 'report.json'), '.'],
            cwd=root, capture_output=True, text=True,
        )
        # Never print scanner output or fixture contents, even on failure.
        assert result.returncode == (1 if expected else 0), (
            f'{path}: unexpected scanner exit code {result.returncode}'
        )
        findings = json.loads((root / 'report.json').read_text()) or []
        assert {finding['RuleID'] for finding in findings} == expected, path
    assert not root.exists(), 'Temporary test fixtures were not removed'


if __name__ == '__main__':
    allowed_paths = (
        'chart/vocabs/values.yaml',
        'environments/example.yaml',
        'environments/vocabs-platform-dev.yaml',
        'docs/rancher.md',
        'tests/gateway/test_gateway.py',
        'tests/helm/test_render.py',
    )
    for path in allowed_paths:
        scan(path, FIELD_NAME, set())
        scan(path, secrets.token_hex(32), {'generic-api-key'})
        scan(path, FIELD_NAME + '-unexpected', {'generic-api-key'})
    scan('other.yaml', FIELD_NAME, {'generic-api-key'})
    # A provider-specific rule must also remain active.
    scan('other.yaml', 'ghp_' + secrets.token_hex(18), {'github-pat'})
    print('Gitleaks: 20 scope/detection checks passed; temporary fixtures removed')
