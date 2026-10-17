# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Development gate for routerops.opnsense; `make venv` once, then `make check`.

SHELL := /bin/bash
VENV := .venv
VENV_OLDEST := .venv-oldest
COLL := build/ansible_collections/routerops/opnsense
BIN ?= $(CURDIR)/$(VENV)/bin

.PHONY: venv collection-tree lint sanity units sanity-oldest units-oldest secrets changelog-lint licences fields fields-test docs docs-generate docs-check check integration

venv:
	python3.12 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements-dev.txt
	python3.12 -m venv $(VENV_OLDEST)
	$(VENV_OLDEST)/bin/pip install -q -r requirements-oldest.txt

collection-tree:
	mkdir -p $(COLL)
	rsync -a --delete --delete-excluded --exclude build --exclude .references --exclude .venv --exclude .venv-oldest --exclude /.git --exclude .superpowers --exclude .agents --exclude .claude --exclude mise.toml ./ $(COLL)/
	cd $(COLL) && git init -q && git add -A

lint:
	$(BIN)/ansible-lint

sanity: collection-tree
	cd $(COLL) && $(BIN)/ansible-test sanity --venv --python 3.12

units: collection-tree
	cd $(COLL) && $(BIN)/ansible-test units --venv --python 3.12

sanity-oldest: collection-tree
	cd $(COLL) && $(CURDIR)/$(VENV_OLDEST)/bin/ansible-test sanity --venv --python 3.12

units-oldest: collection-tree
	cd $(COLL) && $(CURDIR)/$(VENV_OLDEST)/bin/ansible-test units --venv --python 3.12

secrets:
	gitleaks git --no-banner

changelog-lint:
	$(BIN)/antsibull-changelog lint

CATALOG ?= meta/areas.yml

fields:
	bash tools/fetch-fields.sh $(CATALOG) $(ID)

fields-test:
	@for x in tools/tests/fields/*.xml; do \
		node=$$(sed -n '1s/^<!-- node: *\(.*\) -->$$/\1/p' $$x); \
		diff <(bash tools/extract-fields.sh $$x $$node | yq -o json) <(yq -o json $${x%.xml}.expected.yml) || { echo "fields-test failed: $$x" >&2; exit 1; }; \
		test "$$(bash tools/extract-fields.sh $$x $$node | yq '[.. | select(tag == "!!str" and style != "double")] | length')" = 0 || { echo "fields-test: unquoted strings from $$x" >&2; exit 1; }; \
	done
	@for x in tools/tests/fields/fail/*.xml; do \
		node=$$(sed -n '1s/^<!-- node: *\(.*\) -->$$/\1/p' $$x); \
		! bash tools/extract-fields.sh $$x $$node >/dev/null 2>&1 || { echo "fields-test: $$x should fail" >&2; exit 1; }; \
	done
	@for f in meta/fields/*.yml; do \
		test "$$(yq '[.. | select(tag == "!!str" and style != "double")] | length' $$f)" = 0 || { echo "fields-test: unquoted strings in $$f" >&2; exit 1; }; \
	done

licences:
	$(BIN)/reuse lint

DOCS_OUT := build/docs
DOCS_SPLICED := README.md docs/testing.md plugins/modules/item.py plugins/modules/settings.py

docs-generate:
	$(BIN)/ansible-playbook -i localhost, tools/generate-docs.yml -e opnsense_docs_out=$(CURDIR)/$(DOCS_OUT)

docs: docs-generate
	rsync -a --delete $(DOCS_OUT)/docs/areas/ docs/areas/
	for f in $(DOCS_SPLICED); do cp $(DOCS_OUT)/$$f $$f; done

docs-check: docs-generate
	diff -r $(DOCS_OUT)/docs/areas docs/areas
	for f in $(DOCS_SPLICED); do diff -u $(DOCS_OUT)/$$f $$f || exit 1; done

check: lint sanity units sanity-oldest units-oldest secrets changelog-lint licences fields-test docs-check

integration: collection-tree
	@if [ "$$OPNSENSE_INTEGRATION" != "1" ]; then echo "set OPNSENSE_INTEGRATION=1" >&2; exit 1; fi
	@for v in OPNSENSE_URL OPNSENSE_API_KEY OPNSENSE_API_SECRET; do \
		if [ -z "$${!v}" ]; then echo "set $$v" >&2; exit 1; fi; \
	done
	@for f in tests/integration/$(or $(TARGET),test-*).yml; do \
		ANSIBLE_COLLECTIONS_PATH=$(CURDIR)/build $(BIN)/ansible-playbook "$$f" || exit 1; \
	done

-include integration.local.mk
TUNNEL_PORT ?= 18443
BW_ITEM := routerops-opnsense-test

.PHONY: integration-local integration-reset

integration-local: collection-tree
	@test -n "$(PROXMOX_HOST)" || { echo "set PROXMOX_HOST, for example in integration.local.mk" >&2; exit 1; }
	@socat TCP-LISTEN:$(TUNNEL_PORT),bind=127.0.0.1,reuseaddr,fork EXEC:"ssh -o BatchMode=yes root@$(PROXMOX_HOST) nc 10.250.1.1 443" & \
	pid=$$!; trap 'kill $$pid 2>/dev/null' EXIT; \
	for i in $$(seq 60); do curl -sk -o /dev/null https://127.0.0.1:$(TUNNEL_PORT)/ && break; sleep 2; done; \
	bw sync >/dev/null; \
	OPNSENSE_INTEGRATION=1 OPNSENSE_URL=https://127.0.0.1:$(TUNNEL_PORT) OPNSENSE_VALIDATE_CERTS=false \
	OPNSENSE_API_KEY="$$(bw get username $(BW_ITEM))" OPNSENSE_API_SECRET="$$(bw get password $(BW_ITEM))" \
	$(MAKE) --no-print-directory integration TARGET="$(TARGET)"

integration-reset:
	@test -n "$(PROXMOX_HOST)" || { echo "set PROXMOX_HOST, for example in integration.local.mk" >&2; exit 1; }
	@ssh -o BatchMode=yes root@$(PROXMOX_HOST) 'qm rollback 9090 clean && qm start 9090'
