# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Development gate for routerops.opnsense; `make venv` once, then `make check`.

SHELL := /bin/bash
VENV := .venv
COLL := build/ansible_collections/routerops/opnsense
BIN := $(CURDIR)/$(VENV)/bin

.PHONY: venv collection-tree lint sanity units secrets changelog-lint licences check integration

venv:
	python3.12 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements-dev.txt

collection-tree:
	mkdir -p $(COLL)
	rsync -a --delete --exclude build --exclude .references --exclude .venv --exclude .git --exclude .superpowers ./ $(COLL)/

lint:
	$(BIN)/ansible-lint

sanity: collection-tree
	cd $(COLL) && $(BIN)/ansible-test sanity --venv --python 3.12

units: collection-tree
	cd $(COLL) && $(BIN)/ansible-test units --venv --python 3.12

secrets:
	gitleaks git --no-banner

changelog-lint:
	$(BIN)/antsibull-changelog lint

licences:
	$(BIN)/reuse lint

check: lint sanity units secrets changelog-lint licences

integration: collection-tree
	@if [ "$$OPNSENSE_INTEGRATION" != "1" ]; then echo "set OPNSENSE_INTEGRATION=1" >&2; exit 1; fi
	@for v in OPNSENSE_URL OPNSENSE_API_KEY OPNSENSE_API_SECRET; do \
		if [ -z "$${!v}" ]; then echo "set $$v" >&2; exit 1; fi; \
	done
	@for f in tests/integration/$(or $(TARGET),*).yml; do \
		ANSIBLE_COLLECTIONS_PATH=$(CURDIR)/build $(BIN)/ansible-playbook "$$f" || exit 1; \
	done
