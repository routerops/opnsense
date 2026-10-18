# Plan 4c.3: Dnsmasq general, domain override, range and option Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalog entry, field file, integration test and generated section for Dnsmasq general (settings), domain override, DHCP range and DHCP option; the field extractor stops listing item lists as fields.

**Architecture:** One tooling fix (Task 1: `tools/extract-fields.sh` drops `ArrayField` nodes, which the Dnsmasq model root holds next to its fields), then the plan 4c.1 pattern per catalog entry and a closing task. The DHCP option entry is the first to use `always_send` (plan 3c).

**Tech Stack:** as plan 4b.

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Scope" (v0 feature bar: Dnsmasq general, domain override, range, option) and "Module behaviour" (`always_send`: the Dnsmasq DHCP option reads `type`). Tracking: row 4c.3 ("the Dnsmasq DHCP option uses `always_send: [type]` and checks live that an update without `type` fails"). Depends on plan 4c.2. Facts: research of 18.10.2026 against `opnsense/core` tag 26.7.7.

## Global Constraints

- Everything from plan 4c.1's Global Constraints holds, except the Unbound-specific lines; Unbound keeps port 53.
- Dnsmasq stays disabled: no test or example sets `enable: true` with a write that succeeds. The general test changes `dhcp.lease_max` only and restores it in `always`.
- Test data is invented: domains `one.routerops.test`, `two.routerops.test`, example `example.routerops.test`; DNS targets `10.250.1.53`, `10.250.1.54`; ranges on `lan` `10.250.1.100`-`10.250.1.119` and `10.250.1.120`-`10.250.1.139`, example `10.250.1.200`-`10.250.1.219`.
- Catalog ids and test files: `dnsmasq_general`, `dnsmasq_domain_override`, `dnsmasq_range`, `dnsmasq_option`; tests `test-dnsmasq-general-settings.yml`, `test-dnsmasq-domain-override-item.yml`, `test-dnsmasq-range-item.yml`, `test-dnsmasq-option-item.yml`.

### API facts (26.7.7)

All entries: path `dnsmasq/settings`, apply `dnsmasq/service/reconfigure`, model `Dnsmasq/Dnsmasq.xml`, privilege `page-services-dnsforwarder` as `dnsmasq_host` (the API user already holds it).

| Item | module | key | actions | node |
|---|---|---|---|---|
| General | `settings` | `dnsmasq` | `get` `set` (defaults) | root (no `node`) |
| Domain override | `item` | `domainoverride` | `searchDomain` `getDomain` `addDomain` `setDomain` `delDomain` | `domainoverrides` |
| DHCP range | `item` | `range` | `searchRange` `getRange` `addRange` `setRange` `delRange` | `dhcp_ranges` |
| DHCP option | `item` | `option` | `searchOption` `getOption` `addOption` `setOption` `delOption` | `dhcp_options` |

| Fact | Consequence |
|---|---|
| The model root holds 23 fields, the `dhcp` container (14 fields) and six `ArrayField` item lists (`hosts`, `domainoverrides`, `dhcp_tags`, `dhcp_ranges`, `dhcp_options`, `dhcp_boot`); `extract-fields.sh` lists the lists as fields of type `ArrayField` (checked offline 18.10.2026) | Task 1 drops `ArrayField` entries |
| `getAction` adds a pseudo field `dhcp.%domain`; `dns_port` is volatile (SettingsController.php:76-83, Dnsmasq.php:47,55) | key `dnsmasq`; nested fields such as `dhcp.lease_max` |
| A save that changes `enable` or `port` fails while another service holds the DNS port; Unbound reports 53 (Dnsmasq.php:419-439, unbound.inc:51-64); `port: 0` turns DNS off and claims no port (dnsmasq.inc:60-62) | the general test's invalid case is `enable: true` with the default port; the note says to send `port: 0` for DHCP only |
| Every apply also runs `filter reload skip_alias` (ServiceController.php:45-48); an apply with Dnsmasq disabled answers `ok` (`test-dnsmasq-host-item`) | the notes mention the filter reload |
| Domain override: `domain` required (wildcards allowed), `ip` stores `!` as `""` (DomainIPField.php:55-56), `ipset` relates to a firewall alias, the description field is `descr` | lookup `[domain]`; examples never send `ip: "!"` |
| Range: `start_addr` required, `end_addr` required except for static IPv4 ("End address may only be left empty…", Dnsmasq.php:273), `interface` holds the interface name (`lan`) | lookup `[interface, start_addr]` |
| Option: `getOptionOverlay` reads `type` from the request before the write (SettingsController.php:261-264); without it PHP warns and `api.php:32-38,57-59` answers HTTP 500 "Unexpected error, check log for details"; `type: set` blanks `set_tag`, `type: match` blanks `tag`, `interface`, `force`; exactly one of `option`/`option6` (Dnsmasq.php:341-370) | `always_send: [type]`; examples send only fields that fit their type; lookup `[description]` |

## Review Focus

- A DHCP option update that changes only `value`: expect `type` on the wire as well (`always_send`), so the update succeeds; a build without `always_send` gets HTTP 500 (Task 5 fault check).
- A `type: set` option sent with `set_tag`: expect a change on every run, because OPNsense blanks it; the note says so and the examples never send it (Task 5 invalid-shape check asserts the second run still shows `changed`).
- The general test with `enable: true`: expect the validation to stop the write before anything changes, so Unbound keeps port 53 (Task 3 asserts `not changed` and a check-mode read after it still shows `enable: false`).
- A domain override sent with `ip: "!"`: expect drift; the note says to leave `ip` empty instead (no test: forbidden input documented).
- Two ranges with the same `start_addr` on different interfaces: expect two items through the composite lookup (Task 4 note; the VM has one usable interface, so no test).

---

### Task 1: Drop item lists from the field extractor

**Files:**
- Modify: `tools/extract-fields.sh` (the `program` expression)
- Create: `tools/tests/fields/arrays.xml`, `tools/tests/fields/arrays.expected.yml`

**Interfaces:**
- Produces: `extract-fields.sh <xml> ""` on a model root lists fields and one-container-deep fields, never an entry whose type ends in `ArrayField`.

- [ ] **Step 1: Write the failing fixture:** `arrays.xml` (first line `<!-- node:  -->`, root with a `TextField` `name`, a container `dhcp` with a `BooleanField` `local`, and an `ArrayField` `hosts` holding a `TextField` `host`); `arrays.expected.yml` lists only `name` and `dhcp.local`.
- [ ] **Step 2: Run** `make fields-test`. Expected: FAIL "fields-test failed: tools/tests/fields/arrays.xml" (the output holds `hosts`).
- [ ] **Step 3: Implement:** after `flatten(1)`, drop entries whose `+@type` ends in `ArrayField`.
- [ ] **Step 4: Run** `make fields-test` and `make check`. Expected: PASS, every existing `meta/fields/*.yml` unchanged (`make fields` is not rerun).
- [ ] **Step 5: Commit** -> "Drop item lists from the field extractor".

### Task 2: Live facts

**Files:** none committed; a throwaway `tests/integration/facts-dnsmasq.yml`, deleted after the step.

- [ ] **Step 1:** After `make integration-reset`: GET `dnsmasq/settings/get` and print `enable`, `port`, `dhcp.lease_max`; `settings` write of `{enable: true}` -> record the validation key and message (research open question 2); GET `dnsmasq/settings/getOption` (no uuid) and print the option keys for "dns-server" and "ntp-server" (expected `6` and `42`); add an option (`type: set`, `option: <dns-server key>`, `interface: lan`, `value: 10.250.1.1`, `description: routerops facts`), then POST `dnsmasq/settings/setOption/<uuid>` with `{"option": {"value": "10.250.1.2"}}` (no `type`) through `ansible.builtin.uri` and record status and body; then POST `setOption/<uuid>` with `type: set` and `set_tag` set to the uuid of a tag the playbook adds through `dnsmasq/settings/addTag`, GET the option and record whether `set_tag` came back empty. Reset the VM; delete the playbook.

### Task 3: Dnsmasq general

**Files:** `meta/areas.yml`, generated files, `docs/testing.md`; create `meta/fields/dnsmasq_general.yml`, `tests/integration/test-dnsmasq-general-settings.yml`.

- [ ] **Step 1: Catalog entry** `dnsmasq_general`: `area: dnsmasq`, `title: Dnsmasq general`, `module: settings`, values from the tables, no `model.node`, note: "Unbound holds port 53 by default; to run Dnsmasq for DHCP only, send `port: 0` with `enable: true`. Every apply also reloads the firewall rules." Example: "Raise the lease limit" (`dhcp: {lease_max: 2000}`).
- [ ] **Step 2: Run** `make fields ID=dnsmasq_general`, `make docs`. Expected: 37 fields (23 top-level, 14 `dhcp.*`), no `ArrayField`.
- [ ] **Step 3: Write the test** in the plan 4c.1 Task 2 pattern with `dhcp.lease_max` (original + 1); invalid `enable: true` -> `failed`, `not changed`, `validations` holding the key Task 2 recorded and "currently using this port"; `always` restores.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the Dnsmasq general area".

### Task 4: Domain override and range

**Files:** as Task 3 for `dnsmasq_domain_override` and `dnsmasq_range`, tests `test-dnsmasq-domain-override-item.yml`, `test-dnsmasq-range-item.yml`.

- [ ] **Step 1: Catalog entries:** `dnsmasq_domain_override`: `title: Dnsmasq domain override`, `key: domainoverride`, `lookup: [domain]`, note: "Leave `ip` empty to answer NXDOMAIN; `!` is stored as empty and shows a change on every run." Examples: "Send a domain to another server" (`domain: example.routerops.test`, `ip: 10.250.1.53`, `descr: routerops example`), "Remove a domain override". `dnsmasq_range`: `title: Dnsmasq DHCP range`, `key: range`, `lookup: [interface, start_addr]`, note: "The firewall opens DHCP on every interface a range names." Examples: "Add a DHCP range on LAN" (`interface: lan`, `start_addr: 10.250.1.200`, `end_addr: 10.250.1.219`, `description: routerops example`), "Remove a DHCP range".
- [ ] **Step 2: Run** `make fields` for both ids, `make docs`.
- [ ] **Step 3: Write the tests** in the plan 4c.1 Task 3 pattern. Domain override: two overrides from the Global Constraints, update `ip: 10.250.1.55`, invalid `domain: "bad domain"` -> `validations` naming `domainoverride.domain`. Range: two ranges from the Global Constraints, update `lease_time: 3600`, invalid `end_addr: ""` -> `validations` naming `range.end_addr`. Examples twice; cleanup with query.
- [ ] **Step 4:** `make integration-reset`, `make integration-local TARGET=test-dnsmasq-domain-override-item`, then `TARGET=test-dnsmasq-range-item`. Expected: `failed=0` each.
- [ ] **Step 5: Fault check** per test (idempotency). Reset the VM.
- [ ] **Step 6:** `make check`, verified-runs rows, commit -> "Add the Dnsmasq domain override and range areas".

### Task 5: DHCP option

**Files:** as Task 3 for `dnsmasq_option`, test `test-dnsmasq-option-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: Dnsmasq DHCP option`, `key: option`, `lookup: [description]`, `always_send: [type]`, note: "OPNsense reads `type` on every write, so the module always sends it; without it the update fails with HTTP 500. `type: set` clears `set_tag`, `type: match` clears `tag`, `interface` and `force`; send only the fields that fit. Descriptions identify an option; keep them unique." Examples: "Hand out the LAN DNS server" (`type: set`, `option: <dns-server key from Task 2>`, `interface: lan`, `value: 10.250.1.1`, `description: routerops example`), "Remove a DHCP option".
- [ ] **Step 2: Run** `make fields ID=dnsmasq_option`, `make docs`.
- [ ] **Step 3: Write the test** in the plan 4c.1 Task 3 pattern: options `routerops test one` (dns-server, `10.250.1.1`) and `routerops test two` (ntp-server, `10.250.1.1`), both `type: set`, `interface: lan`; update `value: 10.250.1.2` on one (sends only `value` and, through `always_send`, `type`); if Task 2 showed `set_tag` blanked, an extra task sends `routerops test two` with `set_tag` (a tag the test adds and removes) twice and asserts both runs show `changed`; otherwise the note line about `type: set` clearing `set_tag` is dropped and the task is skipped; invalid: neither `option` nor `option6` -> `validations` naming `option.option`; examples twice; cleanup with query.
- [ ] **Step 4: Run** `make integration-reset`, `make integration-local TARGET=test-dnsmasq-option-item`. Expected: `failed=0`.
- [ ] **Step 5: Fault check:** a copy with `always_send: []` must FAIL on the update with HTTP 500 "Unexpected error, check log for details"; a copy with a changed idempotency value must FAIL. Reset the VM.
- [ ] **Step 6:** `make check`, verified-runs row with the HTTP 500 observation, commit -> "Add the Dnsmasq DHCP option area".

### Task 6: Close plan 4c.3 and 4c

**Files:** `docs/superpowers/plans/2026-10-17-v0-tracking.md`, `docs/testing.md`

- [ ] **Step 1:** Tracking row 5, facts for `docs/limits.md`: Dnsmasq and Unbound share port 53 (`port: 0` for DHCP only); every Dnsmasq apply reloads the firewall; the DHCP option needs `type` on every write.
- [ ] **Step 2:** `make integration-reset`, `make integration-local` (everything). Expected: every play `failed=0`. Verified-runs row.
- [ ] **Step 3:** tracking rows 4c.3 -> done; `make check`; commit -> "Close plan 4c".
- [ ] **Step 4:** final whole-branch review (most capable model), fix pass, PR.
