#!/usr/bin/env bash
# Shared tool versions for Helm validation and publishing on ubuntu-24.04.
set -euo pipefail
mkdir -p "$RUNNER_TEMP/vocabs-bin"
curl -fsSL https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz -o "$RUNNER_TEMP/helm.tar.gz"
echo "ee88b3c851ae6466a3de507f7be73fe94d54cbf2987cbaa3d1a3832ea331f2cd  $RUNNER_TEMP/helm.tar.gz" | sha256sum -c -
tar -xzf "$RUNNER_TEMP/helm.tar.gz" -C "$RUNNER_TEMP" linux-amd64/helm
cp "$RUNNER_TEMP/linux-amd64/helm" "$RUNNER_TEMP/vocabs-bin/helm"
curl -fsSL https://github.com/yannh/kubeconform/releases/download/v0.6.7/kubeconform-linux-amd64.tar.gz -o "$RUNNER_TEMP/kubeconform.tar.gz"
echo "95f14e87aa28c09d5941f11bd024c1d02fdc0303ccaa23f61cef67bc92619d73  $RUNNER_TEMP/kubeconform.tar.gz" | sha256sum -c -
tar -xzf "$RUNNER_TEMP/kubeconform.tar.gz" -C "$RUNNER_TEMP/vocabs-bin" kubeconform
echo "$RUNNER_TEMP/vocabs-bin" >> "$GITHUB_PATH"
node --version # Preinstalled on ubuntu-24.04; required for njs logic tests.
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
