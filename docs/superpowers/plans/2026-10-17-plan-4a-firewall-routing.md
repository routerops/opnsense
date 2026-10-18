# Plan 4a: Firewall rules, NAT, static routes and gateways Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalog entry, field file, integration test and generated page for firewall filter rule, destination NAT, source NAT (rules and the outbound NAT mode), one-to-one NAT, static route and gateway, plus the alias -> filter rule scenario; `item` ignores search rows that are not MVC items.

**Architecture:** One module fix (Task 1), then one task per catalog entry following the plan 3 pattern: entry in `meta/areas.yml`, `make fields ID=<id>`, `tests/integration/test-<id>-<module>.yml` reading the entry, `make docs`. Scenario playbooks are named `scenario-*.yml` so the generator's test pairing ignores them; `make integration` runs them after the `test-*.yml` files.

**Tech Stack:** as plan 3c (ansible-core 2.21.5 and 2.20.10, Python 3.12, ansible-test, ansible-lint 26.10.1, yq).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Scope" (v0: firewall filter rule, destination NAT, source NAT, one-to-one NAT, routes static route, routing gateway). Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`, row 4a. Depends on plan 3c (merged as `db0b931`). Facts: research of 17.10.2026 against `opnsense/core` tag 26.7.7, quoted below.

## Global Constraints

- Everything from `AGENTS.md` and plans 3-3c holds: TDD, a new assert counts only after it failed once against a real fault, check mode never writes, a rerun shows `changed=0`, every catalog example runs twice, cleanup in `always` with the post-cleanup query check, every user-visible change gets a fragment.
- Integration runs only against VM 9090 via `make integration-local`; `make integration-reset` before each full run.
- Catalog ids and test files: `firewall_filter_rule`, `firewall_destination_nat`, `firewall_source_nat`, `firewall_source_nat_general` (settings), `firewall_one_to_one_nat`, `routes_static_route`, `routing_gateway`; tests `test-<id with ->-<module>.yml`.
- Test values sit on the VM's networks (LAN 10.250.1.0/24, WAN 10.250.0.2/30, see `docs/testing.md`); descriptions start with `routerops test`; examples use `routerops example`.
- Never send `sequence: 0` (all four firewall areas reject it, minimum 1); leave `sequence` out.
- Write protocol values in the stored case: filter and source NAT `TCP`, destination NAT `tcp`, `any` lower case.

### API facts (26.7.7)

| Item | path | key | actions | apply | model file, node | privilege |
|---|---|---|---|---|---|---|
| Filter rule | `firewall/filter` | `rule` | `searchRule` `getRule` `addRule` `setRule` `delRule` | `firewall/filter/apply` | `Firewall/Filter.xml`, `rules.rule` | `page-filter-api` "Firewall: Rules [new]", `api/firewall/filter/*`, Firewall ACL |
| Destination NAT | `firewall/d_nat` | `rule` | same | `firewall/d_nat/apply` | `Firewall/DNat.xml`, `rule` | `page-firewall-nat-portforward-edit` "Firewall: NAT: Destination NAT", `api/firewall/d_nat/*`, Core ACL |
| Source NAT rule | `firewall/source_nat` | `rule` | same | `firewall/source_nat/apply` | `Firewall/Filter.xml`, `snatrules.rule` | `page-filter-snat-api` "Firewall: NAT: Source NAT", `api/firewall/source_nat/*`, Firewall ACL |
| Outbound NAT mode | `firewall/source_nat` | `filter.general` | `get` `set` (defaults) | `firewall/source_nat/apply` | `Firewall/Filter.xml`, `general` | as source NAT rule |
| One-to-one NAT | `firewall/one_to_one` | `rule` | same as filter | `firewall/one_to_one/apply` | `Firewall/Filter.xml`, `onetoone.rule` | `page-firewall-nat-1-1-edit` "Firewall: NAT: 1:1", `api/firewall/one_to_one/*`, Firewall ACL |
| Static route | `routes/routes` | `route` | `searchroute` `getroute` `addroute` `setroute` `delroute` | `routes/routes/reconfigure` | `Routes/Route.xml`, `route` | `page-system-staticroutes` "System: Static Routes", `api/routes/*`, Core ACL |
| Gateway | `routing/settings` | `gateway_item` | `searchGateway` `getGateway` `addGateway` `setGateway` `delGateway` | `routing/settings/reconfigure` | `Routing/Gateways.xml`, `gateway_item` | `page-system-gateways` "System: Gateways", `api/routing/settings/*`, Core ACL |

Model paths are below `src/opnsense/mvc/app/models/OPNsense/`; ACL files are `<that dir>/Firewall/ACL/ACL.xml` and `<that dir>/Core/ACL/ACL.xml`.

| Fact | Consequence |
|---|---|
| `FilterBaseController::applyAction` returns `['status' => configdRun('filter reload skip_alias')]`, i.e. `"OK\n\n"`; `rc.filter_configure` sets no exit code, so a ruleset pf rejects still answers `OK` | `require_ok` passes; the docs say a firewall apply cannot report a pf load error |
| Routes `reconfigure` returns `ok` or `error reloading routes (...)`; gateway `reconfigure` always returns `ok` on POST | only routes report a real apply failure |
| Search rows that are not MVC items: filter (`legacy: true`, `uuid` = 32-hex md5), destination NAT (`uuid` `automatic_<provider>_<n>`), source NAT in `automatic`/`hybrid` mode (`automatic_<if>`, `automatic_isakmp_<if>`), gateway (generated, `uuid` = gateway name, `virtual: true`); `delGateway` on such a row answers `failed` | Task 1: `item` ignores every row whose `uuid` is not an RFC 4122 UUID, for lookup and purge; without it a lookup can hit such a row and `setRule` on an unknown UUID creates a new item on every run |
| `searchRule` on source NAT lists MVC rules only in `hybrid` or `advanced` mode; the default is `automatic` | the source NAT test sets `hybrid` through `firewall_source_nat_general` and restores the read value in `always` |
| `SourceNatController::setAction` reads `getPost('filter')['general']`; `getAction` returns `{"filter": {"general": {...}}}` | `settings` with dotted key `filter.general` |
| Destination NAT items hold `source{network,port,not}` and `destination{network,port,not}`; `source.address`, `destination.address`, `created`, `categories` are read-only or volatile | examples send nested dicts and none of the read-only fields |
| The route `gateway` field validates against configd `interface gateways list`, cached 20 s and never flushed | the route test creates its gateway before any route request and then pauses 21 s; cleanup deletes the route before the gateway (`delGateway` refuses a gateway a route uses) |
| Gateway `name` is unique and immutable; `gateway` IP is unique and required on an interface with a static address (both VM interfaces are static); `weight` minimum 1 | lookup `name`; tests use `10.250.1.254` on `lan` |
| Only the gateway `name` is unique in the model; filter, NAT and route lookups are not enforced | lookups: filter, source NAT, one-to-one `description`; destination NAT `descr`; route `network` |

## Review Focus

- A filter rule whose description equals an automatic or legacy rule's: expect a new MVC rule on the first run and `changed=0` on the rerun, never a write to the non-MVC row (Task 1 unit test; Task 3 live check).
- `purge` on an area whose search lists non-MVC rows: expect only UUID rows in `purged`, no delete sent for the others (Task 1).
- Source NAT test aborted mid-run: expect the `always` block to restore the outbound NAT mode the test read at the start, not a hard-coded value (Task 5).
- Deleting an alias a filter rule still uses: expect `failed`, `changed=false` and a message naming the rule (Task 9).
- A route test run right after another route request: expect the 21 s pause to keep the gateway validation from failing on the cached gateway list (Task 8).

## Owner step before Task 3

Give the API user `ansible-test` on VM 9090 the six privileges from the table above (in addition to the three it has), shut the VM down, delete the snapshot `clean` and take it again. The agent cannot do this: the test user has no `auth/user` privilege, and the snapshot lives on the owner's Proxmox.

---

### Task 1: `item` ignores search rows that are not MVC items

**Files:**
- Modify: `plugins/modules/item.py` (`find`, the purge loop in `run`, `purge` and `lookup` docs)
- Test: `tests/unit/plugins/modules/test_item.py`
- Create: `changelogs/fragments/item-non-mvc-rows.yml` (`bugfixes`)

**Interfaces:**
- Produces: `MVC_UUID` (compiled regex `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`, case-insensitive) and `Run.mvc_rows(rows) -> list` in `item.py`; `find` and the purge loop use `mvc_rows(search["rows"])`.

- [ ] **Step 1: Switch the fake row ids to UUIDs.** The existing tests use ids such as `u1`, `h1`, which the fix would ignore. Replace each with a constant (`U1 = "00000000-0000-4000-8000-000000000001"` and so on) with `sed -E`, then run `make units`. Expected: PASS (pure rename).
- [ ] **Step 2: Write the failing tests**: `test_lookup_ignores_non_mvc_rows` (rows: `{"uuid": "0123456789abcdef0123456789abcdef", "legacy": true, "name": "web", ...}` plus nothing else; expect `addItem` sent, no `setItem`, outcome `added`), `test_purge_skips_non_mvc_rows` (rows: one listed UUID row, one `automatic_wan_1`, one `WAN_DHCP` row; expect `purged == []` and no `del` request), `test_lookup_still_matches_uppercase_uuid` (a row with an upper-case UUID matches).
- [ ] **Step 3: Run** `make units`. Expected: the first two FAIL (`setItem` sent; `delItem` sent), the third PASS (pins behaviour).
- [ ] **Step 4: Implement** `MVC_UUID` and `mvc_rows`; `check_row` runs only on MVC rows. Docs: `purge` gains "Rows whose C(uuid) is not a UUID, such as automatic filter rules or generated gateways, are not MVC items; O(purge) and the lookup ignore them." and drops nothing else.
- [ ] **Step 5: Run** `make units` and `make check`. Expected: PASS.
- [ ] **Step 6: Commit** with the fragment -> "Ignore search rows that are not MVC items".

### Task 2: Scenario playbooks in `make integration`

**Files:**
- Modify: `Makefile` (`integration`), `docs/testing.md` ("Run")

- [ ] **Step 1:** `integration` loops over `tests/integration/$(or $(TARGET),test-*).yml` and then, when `TARGET` is unset, over `tests/integration/scenario-*.yml` (skip the glob when it matches nothing). `docs/testing.md` "Run": one sentence that scenario playbooks run after the area tests and take `TARGET=scenario-<name>` alone.
- [ ] **Step 2: Run** `make -n integration OPNSENSE_INTEGRATION=1` with dummy env vars. Expected: no scenario line yet (no file), no error.
- [ ] **Step 3: Commit** with Task 9 (the first scenario), not alone.

### Task 3: Firewall filter rule

**Files:**
- Modify: `meta/areas.yml`, generated files (`make docs`)
- Create: `meta/fields/firewall_filter_rule.yml` (`make fields ID=firewall_filter_rule`), `tests/integration/test-firewall-filter-rule-item.yml`

- [ ] **Step 1: Catalog entry** `firewall_filter_rule`: values from the API facts table, `lookup: [description]`, `stage: v0`, `tested: ["26.7.7"]`, examples: "Allow HTTPS to the firewall from LAN" (`interface: lan`, `protocol: TCP`, `source_net: lan`, `destination_net: (self)`, `destination_port: "443"`, `description: routerops example https`), "Block a host on LAN" (`action: block`, `source_net: 10.250.1.99`, `description: routerops example block`), "Remove a filter rule" (`description: routerops example block`, `state: absent`). No `purge` example.
- [ ] **Step 2: Run** `make fields ID=firewall_filter_rule` and `make docs`. Expected: `meta/fields/firewall_filter_rule.yml`, `docs/areas/firewall.md` gains the section; `make docs-check` fails until the test exists ("needs tests/integration/test-firewall-filter-rule-item.yml").
- [ ] **Step 3: Write the test** after `test-dnsmasq-host-item.yml`: two rules (`routerops test one`, `routerops test two`), check-mode add, add, rerun `changed=0`, check-mode rerun, update `destination_port`, delete, invalid (`destination_port` with `protocol: any` -> `validations`), examples twice, cleanup with post-cleanup query. Extra asserts: the apply after the add did not fail (the module checks `status`; add `opnsense_test_add is not failed`), and a check-mode `purge: true` with the two test rules listed reports only UUIDs in `purged` (`purged | reject('match', uuid_regex) | list == []`).
- [ ] **Step 4: Run** `make integration-reset` then `make integration-local TARGET=test-firewall-filter-rule-item`. Expected: `failed=0`.
- [ ] **Step 5: Fault check.** Build the collection from `main` (before Task 1) into a scratch tree and run the test copy against it: the purge assert must FAIL if the VM lists automatic rules (record whether it does); then a copy with a changed wanted value in the idempotency task must FAIL. Reset the VM after.
- [ ] **Step 6:** `make check`; record the run in `docs/testing.md` "Verified runs" (one row, with the purge observation); commit -> "Add the firewall filter rule area".

### Task 4: Firewall destination NAT

**Files:** as Task 3 for `firewall_destination_nat`, test `test-firewall-destination-nat-item.yml`.

- [ ] **Step 1: Catalog entry:** `lookup: [descr]`; examples "Forward port 8080 on WAN to a LAN web server" (`interface: wan`, `protocol: tcp`, `destination: {network: wanip, port: "8080"}`, `target: 10.250.1.50`, `local-port: "80"`, `descr: routerops example web`), "Remove a port forward" (`descr`, plus the fields the lookup needs, `state: absent`).
- [ ] **Step 2: Run** `make fields ID=firewall_destination_nat`, `make docs`. Expected as Task 3; the field file lists `source.*` and `destination.*`.
- [ ] **Step 3: Write the test** (pattern of Task 3; update changes `destination.port`; invalid: `destination.port` with `protocol: ""` -> `validations`). Assert that the rerun after the nested update is unchanged.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the firewall destination NAT area".

### Task 5: Outbound NAT mode and source NAT rules

**Files:** catalog entries `firewall_source_nat_general` and `firewall_source_nat`; field files; tests `test-firewall-source-nat-general-settings.yml`, `test-firewall-source-nat-item.yml`.

- [ ] **Step 1: Catalog entries.** `firewall_source_nat_general`: `module: settings`, key `filter.general`, apply `firewall/source_nat/apply`, model node `general`, example "Use hybrid outbound NAT" (`snat_mode: hybrid`). `firewall_source_nat`: `lookup: [description]`, examples "Translate a LAN subnet on WAN" (`interface: wan`, `source_net: 10.250.1.0/24`, `description: routerops example lan`), "Remove a source NAT rule".
- [ ] **Step 2: Run** `make fields` for both ids, `make docs`.
- [ ] **Step 3: Settings test:** read the mode by running `settings` in check mode with `snat_mode: hybrid` and storing `settings['snat_mode']` (the value read before any write) as the original, set `hybrid`, rerun `changed=0`, set `advanced`, examples twice, restore the original in `always`.
- [ ] **Step 4: Item test:** a first block task reads and stores the mode as in Step 3 and sets `hybrid`; then the Task 3 pattern; `always` restores the stored mode after the item cleanup. Extra assert: the item rerun is `changed=0` (proves the search lists the rule; in `automatic` mode it would add a duplicate).
- [ ] **Step 5: Fault check:** a copy that skips the mode switch must FAIL on the rerun assert (duplicate add). Reset the VM.
- [ ] **Step 6:** spec "Scope" v0 row: add "Firewall: outbound NAT mode (`source_nat` general), which source NAT rules need". `make check`, verified-runs rows, commit -> "Add the source NAT areas".

### Task 6: Firewall one-to-one NAT

**Files:** as Task 3 for `firewall_one_to_one_nat`, test `test-firewall-one-to-one-nat-item.yml`.

- [ ] **Step 1: Catalog entry:** `lookup: [description]`; examples "Map a LAN host to a WAN address" (`source_net: 10.250.1.50`, `external: 10.250.0.50`, `description: routerops example one`), "Keep only the listed one-to-one rules" (`purge: true`, the first plus `10.250.1.51` -> `10.250.0.51`), "Remove a one-to-one rule".
- [ ] **Step 2-6:** as Task 3 (invalid: `source_net: 10.250.1.0/24` with `external: 10.250.0.50` -> prefix mismatch `validations`), commit -> "Add the one-to-one NAT area".

### Task 7: Gateway

**Files:** as Task 3 for `routing_gateway`, test `test-routing-gateway-item.yml`.

- [ ] **Step 1: Catalog entry:** `area: routing`, `lookup: [name]`; examples "Add a LAN gateway" (`name: RT_EXAMPLE_GW`, `interface: lan`, `gateway: 10.250.1.254`, `descr: routerops example`), "Remove a gateway". No `purge` example (generated gateways belong to OPNsense).
- [ ] **Step 2-3:** fields, docs, test (two gateways `10.250.1.253`/`.252`; update `descr`; invalid `weight: 0` -> `validations`; check-mode `purge` lists only UUIDs, as Task 3).
- [ ] **Step 4-6:** run, fault check, `make check`, verified-runs row, commit -> "Add the gateway area".

### Task 8: Static route

**Files:** as Task 3 for `routes_static_route`, test `test-routes-static-route-item.yml`.

- [ ] **Step 1: Catalog entry:** `area: routes`, `lookup: [network]`; examples "Route a remote network through a LAN gateway" (`network: 10.99.0.0/24`, `gateway: RT_EXAMPLE_GW`, `descr: routerops example`), "Keep only the listed static routes" (`purge: true`, plus `10.99.1.0/24`), "Remove a static route". The page notes that the gateway must exist first.
- [ ] **Step 2-3:** fields, docs; the test first adds `RT_EXAMPLE_GW` with `routerops.opnsense.item` and the `routing_gateway` entry, then pauses 21 s (`ansible.builtin.pause`, task name says why), then runs the Task 3 pattern (invalid: `network: 10.99.0.0` without prefix -> `validations`); `always` removes routes before the gateway.
- [ ] **Step 4-6:** run, fault check, `make check`, verified-runs row, commit -> "Add the static route area".

### Task 9: Scenario alias -> filter rule

**Files:**
- Create: `tests/integration/scenario-alias-filter-rule.yml`
- Modify: `docs/testing.md` (verified runs)

- [ ] **Step 1: Write the scenario:** add a host alias `rt_scenario_hosts` (catalog `firewall_alias`), add a filter rule with `destination_net: rt_scenario_hosts` (catalog `firewall_filter_rule`), rerun both `changed=0`, try to delete the alias (`ignore_errors`), assert `failed`, `not changed` and `'rt_scenario_hosts' in msg or 'routerops test scenario' in msg`; `always`: delete the rule, then the alias, then query both and assert gone.
- [ ] **Step 2: Run** `make integration-local TARGET=scenario-alias-filter-rule`. Expected: `failed=0` (one ignored expected failure).
- [ ] **Step 3: Fault check:** a copy that deletes the alias without the rule using it must FAIL on the `failed` assert.
- [ ] **Step 4:** `make check`; commit with Task 2 -> "Run scenario playbooks and add alias -> filter rule".

### Task 10: Close plan 4a

**Files:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, `docs/superpowers/plans/2026-10-17-v0-tracking.md`, `docs/testing.md`

- [ ] **Step 1:** Spec "Scope": the 0.x row gains the writable core APIs the spec does not name yet, from the 26.7.7 inventory: Kea DHCPv4 options, Unbound advanced and DNS over TLS, syslog general, IPsec general and charon, interface settings, NetFlow, system health, log view templates, host discovery, alias GeoIP URL. `docs/limits.md` facts for plan 5 in the tracking row 5: a firewall apply answers `OK` even when pf rejects the ruleset; a gateway apply always answers `ok`; source NAT rules need `hybrid` or `advanced` mode.
- [ ] **Step 2:** `make integration-reset`, then `make integration-local` (all tests and the scenario). Expected: every play `failed=0`. Verified-runs row for the full run.
- [ ] **Step 3:** tracking row 4a -> done; `make check`; commit -> "Close plan 4a".
- [ ] **Step 4:** final whole-branch review (most capable model), fix pass, PR.
