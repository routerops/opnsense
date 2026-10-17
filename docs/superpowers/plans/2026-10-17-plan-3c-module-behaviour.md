# Plan 3c: Module behaviour before the v0 areas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the module and client gaps the v0 areas of plan 4 would hit: clear auth and in-use errors, `changed` after a saved write whose apply fails, environment-variable fallbacks, fields that must always be sent, readable secrets kept out of diffs and returns, and read-back values (such as a CA `refid`) per item.

**Architecture:** All changes sit in `plugins/module_utils/_client.py`, `_common.py`, `plugins/doc_fragments/connection.py` and the two modules; the catalog gains two area traits (`always_send`, `secret_fields`) that the generator passes into the examples and the integration tests pass into `module_defaults`. Each behaviour is proven by unit tests with mocked HTTP; the integration tests prove what the current areas can show.

**Tech Stack:** as plan 3 (ansible-core 2.21.5, Python 3.12, ansible-test, ansible-lint 26.10.1).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "The two modules". Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`. Depends on plans 3 and 3b (PR #3). Source: the gap analysis against `matthew-on-git/terraform-provider-opnsense` of 17.10.2026, facts re-checked against `opnsense/core` at tag 26.7.7.

## Global Constraints

- Everything from `AGENTS.md` and the earlier plans holds: check mode never writes, `changed` only on a real write, one apply per call, secrets carry `no_log` and never reach a diff, full `DOCUMENTATION`/`RETURN` with `version_added: "0.1.0"`, every user-visible change gets a fragment.
- New options take these exact names: `always_send`, `secret_fields`, `return_fields` (lists of field names, default `[]`); item `state` gains `query`. `secret_fields` carries `no_log=False` (its name only looks secret).
- The return structure stays stable: every outcome gains `fields` (dict, `{}` when nothing is asked or nothing exists).
- No new module, no area-specific code: every behaviour is driven by an option.

### API facts (26.7.7, code-verified by the gap analysis)

| Fact | Source |
|---|---|
| A failed login answers HTTP 401 with `{"status": 401, "message": "Authentication Failed"}`; an ACL denial HTTP 403 with `{"status": 403, "message": "Forbidden"}`; neither carries `errorMessage` | `controllers/OPNsense/Base/ApiControllerBase.php` |
| A `UserException` (delete of an item in use) answers HTTP 500 with `errorMessage` (the referencing items) and `errorTitle` | `ApiMutableModelControllerBase.php` `delBase`, `www/api.php` |
| A `validations` entry is a list when a field has several messages | `ApiMutableModelControllerBase.php` `validate()` |
| The Dnsmasq option controller reads `option.type` from the POST body to clear dependent fields; an update without `type` skips that | `controllers/OPNsense/Dnsmasq/Api/SettingsController.php` `getOptionOverlay` |
| WireGuard server `privkey`, client `psk` and the IPsec PSK `Key` are ordinary fields that `get` returns; only fields such as the user `password` (`UpdateOnlyTextField`) are never returned | `Wireguard/Server.xml`, `Wireguard/Client.xml`, `IPsec/IPsec.xml`, `Auth/User.xml` |
| OpenVPN and IPsec reference certificates and CAs by `refid` (a `CertificateField`), which OPNsense generates on create | `OpenVPN/OpenVPN.xml`, `Base/FieldTypes/CertificateField.php`, `Trust/Api/CaController.php` |

## Review Focus

- A secret field whose value changes: expect `changed`, and neither the old nor the new value in `diff`, `outcomes` or `settings` (Task 5).
- A query for an item that does not exist: expect `uuid: null`, `fields: {}`, `changed: false` and no write, also outside check mode (Task 6).
- An apply that fails after a saved write in `settings`: expect `failed`, `changed: true` and a message that says the values were saved (Task 2).
- `always_send` naming a field the item does not list: expect a failure before any request, naming the field (Task 4).
- Connection options from the environment with a module argument also set: expect the argument to win (Task 3).

---

### Task 1: Client error messages

**Files:**
- Modify: `plugins/module_utils/_client.py`
- Test: `tests/unit/plugins/module_utils/test_client.py`
- Create: `changelogs/fragments/client-error-messages.yml`

**Interfaces:**
- Produces: messages `authentication failed for <METHOD> <url>; check api_key and api_secret` (401), `<METHOD> <url> is forbidden; the API user lacks the privilege for <path>, which the area page lists under Privileges` (403), `<errorTitle>: <errorMessage>` when both are present.

- [ ] **Step 1: Write the failing tests**: `test_401_names_the_credentials`, `test_403_names_the_privilege`, `test_error_title_joins_message` (HTTP 500 body `{"errorMessage": "alias in use by: rule 1", "errorTitle": "Item in use by"}`), `test_validations_list_passes_through` (a `setItem` answer with `{"result": "failed", "validations": {"alias.name": ["a", "b"]}}` keeps the list in `OPNsenseError.validations`).
- [ ] **Step 2: Run** `make units`. Expected: the first three FAIL on the message text; the fourth may already pass (it pins existing behaviour).
- [ ] **Step 3: Implement** in `_error_message` / `_request`: read `message` as well as `errorMessage` and `errorTitle` from the JSON body; build the texts above for 401 and 403.
- [ ] **Step 4: Run** `make units`. Expected: PASS.
- [ ] **Step 5: Commit** with the fragment (`minor_changes`) -> "Explain auth, privilege and in-use errors".

### Task 2: `changed` after a saved write whose apply fails

**Files:**
- Modify: `plugins/modules/item.py` (`main`), `plugins/modules/settings.py` (`main`)
- Test: `tests/unit/plugins/modules/test_item.py`, `test_settings.py`
- Create: `changelogs/fragments/apply-failure-changed.yml` (`bugfixes`)

- [ ] **Step 1: Write the failing tests**: `test_apply_failure_after_write_reports_changed` (item: one add answers `saved`, the apply answers `{"status": "failed", "status_msg": "x"}`; expect `failed`, `changed is True`, message containing `already saved but not applied`), `test_settings_apply_failure_reports_saved` (same for settings, message containing `saved but not applied`).
- [ ] **Step 2: Run** `make units`. Expected: both FAIL (`changed` missing; settings message lacks the hint).
- [ ] **Step 3: Implement**: item passes `changed=bool(run.saved)` to `fail_json`; settings tracks whether `set` answered `saved`, then on a failed apply appends `; saved but not applied` and passes `changed=True`.
- [ ] **Step 4: Run** `make units`. Expected: PASS.
- [ ] **Step 5: Commit** -> "Report changed when an apply fails after a saved write".

### Task 3: Environment-variable fallbacks

**Files:**
- Modify: `plugins/module_utils/_common.py` (`CONNECTION_ARGSPEC`), `plugins/doc_fragments/connection.py`, the three integration playbooks, `tools/templates/example.yml.j2` (unchanged connection lines; check only), `docs/testing.md` if it names the module defaults
- Test: `tests/unit/plugins/modules/test_settings.py`
- Create: `changelogs/fragments/connection-env.yml`

**Interfaces:**
- Produces: `url` <- `OPNSENSE_URL`, `api_key` <- `OPNSENSE_API_KEY`, `api_secret` <- `OPNSENSE_API_SECRET`, `validate_certs` <- `OPNSENSE_VALIDATE_CERTS` (through `env_fallback`); a module argument wins over the variable.

- [ ] **Step 1: Write the failing tests**: `test_connection_from_environment` (no `url`/`api_key`/`api_secret` arguments, the three variables set with `monkeypatch.setenv`; the client is built with them), `test_argument_wins_over_environment`.
- [ ] **Step 2: Run** `make units`. Expected: the first FAILS (missing required arguments).
- [ ] **Step 3: Implement** the fallbacks; document each under `env:` in the doc fragment; drop the four `lookup('ansible.builtin.env', ...)` lines from the integration playbooks' `module_defaults`.
- [ ] **Step 4: Run** `make check`. Expected: PASS (`validate-modules` accepts the fragment).
- [ ] **Step 5: Commit** -> "Read connection options from the environment".

### Task 4: `always_send` (item)

**Files:**
- Modify: `plugins/modules/item.py` (option, `check_options`, `update`), `meta/areas.yml` schema only, `tools/generate-docs.yml` (schema key `always_send`, list of str; field-name check covers it), `tools/templates/example.yml.j2` (emit when non-empty), `tools/templates/area.md.j2` (settings row "Always sent"), integration playbooks (`always_send: "{{ opnsense_test_area['always_send'] | default([]) }}"`)
- Test: `tests/unit/plugins/modules/test_item.py`
- Create: `changelogs/fragments/item-always-send.yml`

**Interfaces:**
- Produces: on every set of an item, the fields named in `always_send` are sent with their wanted values along with the changed fields; they never cause a write on their own.

- [ ] **Step 1: Write the failing tests**: `test_always_send_rides_along_with_a_change` (the set payload holds the changed field and `type`), `test_always_send_alone_does_not_write` (no change -> no set request), `test_always_send_field_not_listed_fails` (an item without `type` in its `fields` -> failure naming `type` before any request).
- [ ] **Step 2: Run** `make units`. Expected: FAIL (unknown option).
- [ ] **Step 3: Implement**, document the option (Dnsmasq option `type` as the reason), wire the catalog key through generator, templates and playbooks.
- [ ] **Step 4: Run** `make check`. Expected: PASS; generated docs unchanged (no entry sets the key yet).
- [ ] **Step 5: Commit** -> "Add always_send for fields a controller reads on every set".

### Task 5: `secret_fields` (item and settings)

**Files:**
- Modify: `plugins/modules/item.py`, `plugins/modules/settings.py`, `plugins/doc_fragments/` (shared option text in a new fragment `fields.py` if both modules need the same text), catalog schema, generator (key `secret_fields`, list of str, checked against the model), `example.yml.j2`, `area.md.j2` (`(secret)` suffix in the field table), integration playbooks, `meta/areas.yml` (`firewall_alias`: `secret_fields: [password]`), `tests/integration/test-firewall-alias-item.yml`
- Test: `tests/unit/plugins/modules/test_item.py`, `test_settings.py`
- Create: `changelogs/fragments/secret-fields.yml`

**Interfaces:**
- Produces: a field named in `secret_fields` is compared like any other field; its values are added to `module.no_log_values` and replaced by `********` in `diff`, `outcomes` and `settings`.

- [ ] **Step 1: Write the failing tests**: `test_secret_change_is_written_but_masked` (item: stored `privkey` differs from wanted; expect a set request with the wanted value, `changed`, and `********` for both sides in `diff`), `test_secret_unchanged_is_idempotent`, `test_settings_secret_masked_in_settings_return`.
- [ ] **Step 2: Run** `make units`. Expected: FAIL (unknown option).
- [ ] **Step 3: Implement** and document; the doc says that `write_only` is for fields OPNsense never returns and `secret_fields` for readable secrets.
- [ ] **Step 4: Live**: the alias test adds a `urltable` alias with `username` and `password` (`EXAMPLE` values), reruns with `changed=0`, changes the password (`changed`), and asserts that no task result contains either password value. Run `make integration-reset && make integration-local TARGET=test-firewall-alias-item`, then `make integration-reset`. Expected: `failed=0`. Fault copy: drop `password` from `secret_fields` -> the leak assert FAILS.
- [ ] **Step 5: Run** `make docs && make check`, commit -> "Add secret_fields for secrets OPNsense returns".

### Task 6: `return_fields` and `state: query` (item)

**Files:**
- Modify: `plugins/modules/item.py` (options, outcome `fields`, query path), `tests/integration/test-firewall-alias-item.yml`, `meta/areas.yml` (`firewall_alias` example "Read a built-in alias": item `bogons` with `state: query`, example `return_fields: [type]`), `example.yml.j2` (emit `return_fields` when an example sets it), generator schema (example key `return_fields`, list of str; item `state` choices gain `query`), `docs/areas/firewall.md` and `plugins/modules/item.py` `EXAMPLES` (regenerated)
- Test: `tests/unit/plugins/modules/test_item.py`
- Create: `changelogs/fragments/item-return-fields.yml`

**Interfaces:**
- Produces: `return_fields` names fields whose current values (normalised, after any write; secrets masked) each outcome returns under `fields`; an item with `state: query` is looked up and never written, its outcome action is `queried`, `uuid` is `null` when no item matches. After an add, the values are read with one get by the new UUID; in check mode an added item has `fields: {}`.

- [ ] **Step 1: Write the failing tests**: `test_return_fields_after_add` (get after add returns `refid`), `test_return_fields_on_unchanged_item_needs_no_extra_request`, `test_query_found`, `test_query_not_found_does_not_write`, `test_query_ignores_purge` (a queried item counts as listed, so `purge` keeps it), `test_return_field_not_in_model_fails`.
- [ ] **Step 2: Run** `make units`. Expected: FAIL.
- [ ] **Step 3: Implement** and document (`refid` for certificates as the motivating case).
- [ ] **Step 4: Live**: the alias test queries `bogons` with `return_fields: [type]` (expect `type == 'external'` or the value the 26.7.7 VM returns; read it once and pin it), queries a missing alias (`uuid` null), and adds an alias with `return_fields: [name]`. Fault copy: query with a wrong expected `type` -> FAIL. Reset the VM before and after.
- [ ] **Step 5: Run** `make docs && make check`, commit -> "Return read-back fields and allow query-only items".

### Task 7: Spec, tracking, full live run

**Files:**
- Modify: `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md` ("Both modules": readable secrets go in `secret_fields`, `write_only` only for fields never returned; references may be a `refid` read through `return_fields`; `always_send`; `state: query`; environment fallbacks replace the "Left to the builder" line), `docs/superpowers/plans/2026-10-17-v0-tracking.md` (row 3c `done`; plan 4 row gains: Dnsmasq option uses `always_send: [type]` and checks the HTTP 500 without `type` live; WireGuard and IPsec keys use `secret_fields`; Trust create inputs go in `write_only`; cross-area scenario playbooks that pass a `uuid` or `refid`; plan 5 row gains the `docs/limits.md` facts: `flock` on config.xml, non-MVC rows in filter and gateway searches, `set_item` upsert, gateway groups API in 26.7.7, and the upstream register with recheck step), `docs/testing.md` (verified runs)

- [ ] **Step 1: Run** `make integration-reset && make integration-local`, then `make integration-reset`. Expected: all plays `failed=0`.
- [ ] **Step 2: Update spec, tracking and verified runs; run** `make check`. Expected: PASS.
- [ ] **Step 3: Commit** -> "Record plan 3c".
