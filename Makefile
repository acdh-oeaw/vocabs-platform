SHELL := /bin/bash
PYTHON ?= python3
CHART := ./chart/vocabs
.PHONY: deps lint template validate test rdf configmap images

deps:
	@echo "No Helm dependencies to build."
lint:
	helm lint $(CHART)
template:
	helm template vocabs $(CHART) -f environments/example.yaml
validate:
	PYTHON=$(PYTHON) bash scripts/validate.sh
test:
	$(PYTHON) tests/test_theme.py
	$(PYTHON) tests/helm/test_render.py
	$(PYTHON) tests/test_load.py
	$(PYTHON) tests/gateway/test_gateway.py
	node tests/gateway/redirects.mjs
rdf:
	$(PYTHON) scripts/validate-rdf.py
configmap:
	PYTHON=$(PYTHON) bash scripts/configmap.sh "$(VALUES)" "$(NAMESPACE)" "$(CONFIGMAP)" $(TTL_FILES)
images:
	$(PYTHON) scripts/build-images.py --java-base "$(JAVA_BASE_IMAGE)"
