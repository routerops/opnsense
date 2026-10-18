# Plan 4c.1: Unbound Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalog entry, field file, integration test and generated page for Unbound general (settings), host override, host alias, query forward and ACL, plus the host override -> host alias scenario.

**Architecture:** No module change: `settings` already takes a dotted `key` (`unbound.general`) and every item uses its own action names through `actions`. One task per catalog entry in the plan 4b pattern (entry in `meta/areas.yml`, `make fields ID=<id>`, `tests/integration/test-<id>-<module>.yml` reading the entry, `make docs`), one scenario playbook, and a closing task.

**Tech Stack:** as plan 4b (ansible-core 2.21.5 and 2.20.10, Python 3.12, ansible-test, ansible-lint 26.10.1, yq).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Scope" (v0: Unbound general, host override, host alias, forward, ACL). Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`, row 4c.1. Depends on plan 4b (merged as `2e606a9`). Followed by plan 4c.2 (`2026-10-18-plan-4c2-kea.md`) and 4c.3 (`2026-10-18-plan-4c3-dnsmasq.md`). Facts: research of 18.10.2026 against `opnsense/core` tag 26.7.7, quoted below.

## Global Constraints

- Everything from `AGENTS.md` and plans 3-4b holds: TDD, a new assert counts only after it failed once against a real fault, check mode never writes, a rerun shows `changed=0`, every catalog example runs twice, cleanup in `always` with the post-cleanup query check, every user-visible change gets a fragment.
- Integration runs only against VM 9090 via `make integration-local`; `make integration-reset` before each full run.
- Unbound stays enabled on port 53: no test or example changes `unbound.general` `enabled`, `port`, `active_interface` or `outgoing_interface`. The general test changes `txtsupport` only and restores it in `always`.
- Test data is invented (spec, "Privacy"): domain `routerops.test`, host names `rt-test-one`, `rt-test-two`, `rt-example`; servers `10.250.1.20` and `10.250.1.21`; forward servers `10.250.1.53`, `10.250.1.54`; ACL networks `10.250.70.0/24`, `10.250.71.0/24`. Descriptions `routerops test one` / `two`, examples `routerops example`.
- Catalog ids and test files: `unbound_general`, `unbound_host_override`, `unbound_host_alias`, `unbound_forward`, `unbound_acl`; tests `test-<id>-<module>.yml` with the id's `_` written as `-` (`test-unbound-host-override-item.yml`); scenario `scenario-host-override-alias.yml`.

### API facts (26.7.7)

All items: path `unbound/settings`, apply `unbound/service/reconfigure`, model `Unbound/Unbound.xml`, privilege `page-services-unbound` "Services: Unbound", `api/unbound/*`, `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Unbound/ACL/ACL.xml`.

| Item | module | key | actions | apply | node |
|---|---|---|---|---|---|
| General | `settings` | `unbound.general` | `get` `set` (defaults) | `unbound/service/reconfigureGeneral` | `general` |
| Host override | `item` | `host` | `searchHostOverride` `getHostOverride` `addHostOverride` `setHostOverride` `delHostOverride` | default | `hosts.host` |
| Host alias | `item` | `alias` | `searchHostAlias` `getHostAlias` `addHostAlias` `setHostAlias` `delHostAlias` | default | `aliases.alias` |
| Forward | `item` | `dot` | `searchForward` `getForward` `addForward` `setForward` `delForward` | default | `dots.dot` |
| ACL | `item` | `acl` | `searchAcl` `getAcl` `addAcl` `setAcl` `delAcl` | default | `acls.acl` |

| Fact | Consequence |
|---|---|
| `page-services-dnsresolver` and `page-services-dnsresolver-acls` cover only `api/unbound/general/*` and `api/unbound/acl/*`, which are no controllers; `-overrides` lacks `service/reconfigure` (ACL.xml:2-46) | every entry names `page-services-unbound` |
| `get`/`set` work on the whole `unbound` model (SettingsController.php:38-39); the UI posts `unbound.general.*` and applies `reconfigureGeneral`, which runs `dns reload`, the restart and `dhcpd restart` (ServiceController.php:61-73) | `settings` key `unbound.general`, apply `unbound/service/reconfigureGeneral`; `get` also returns hosts and ACLs, only wanted fields are compared |
| Every apply forces a stop and start of Unbound (ApiMutableServiceControllerBase.php:147-150, 186-232) and answers `{"status":"ok"}` or `failed` with `status_msg` | the area notes say DNS drops for a moment on every apply; the tunnel does not use DNS |
| A save that changes `enabled` or `port` fails when another service reports the port (Unbound.php:44-63) | see Global Constraints |
| Host override: `hostname` and `domain`, `rr` `A`/`AAAA`/`MX`/`TXT` default `A`, `server` for A/AAAA, `addptr` default `1`, no unique constraint; a hostname ending in `.` is refused (XML:314-424, Unbound.php:89-98) | lookup `[hostname, domain]`; examples use `rr: A` |
| Host override `aliases` is a volatile `AliasReflector`: setting it adds or deletes alias items (AliasReflector.php:70-120); search rows carry `isAlias` and `_children` | never send `aliases`; the host override note points to `unbound_host_alias` |
| `delHostOverride` deletes the host's aliases first (SettingsController.php:222-234) | the scenario asserts it; the note says so |
| Host alias: `host` relates to `hosts.host` (uuid), `hostname` or `domain` required, an empty `domain` inherits the host's; search rows hold the uuid in `host` and the host's description in `%host` (XML:425-467, UIModelGrid.php:136-141) | lookup `[host, hostname]`; the test registers the host uuid |
| Forward and DNS over TLS share `dots.dot`; the action name sets `type` (`addBase(..., ["type" => ...])`, 157-178), a sent `type` is overwritten; search filters by type | never send `type`; DNS over TLS is out of scope (0.x); lookup `[domain, server]`; `domain` empty means all domains |
| ACL: `name` and `networks` (CIDR list) required, `action` default `allow`, `name` not unique | lookup `[name]` |

## Review Focus

- A host override rerun with `aliases` left out: expect `changed=0`, because `aliases` is volatile and not compared (Task 3 rerun assert).
- A host alias whose host was deleted in the GUI: expect the lookup to find nothing and the add to fail on `alias.host`, never to attach the alias to another host (Task 4 invalid task uses an unknown uuid).
- A forward item with the same `domain` and `server` as a DNS over TLS item: expect the forward search not to see it, so the add creates a forward item (Task 5 note; no test, DNS over TLS is 0.x).
- The general test interrupted after the write: expect `always` to restore `txtsupport` even when an assert failed (Task 2, fault check proves it).
- An ACL whose `networks` order differs from the stored one: expect `changed=0`, because only fields in `ordered_fields` compare in order and the entry names none (Task 6 rerun with reversed order).

## Owner step before Task 1

Give the API user `ansible-test` on VM 9090 the privileges `page-services-unbound` ("Services: Unbound") and `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", needed by plan 4c.2) in addition to the ones it has, shut the VM down, delete the snapshot `clean` and take it again. The agent cannot do this (no `auth/user` privilege, the snapshot lives on the owner's Proxmox).

---

### Task 1: Live facts

**Files:** none committed; a throwaway playbook `tests/integration/facts-unbound.yml`, deleted after the step.

- [ ] **Step 1:** After `make integration-reset`, run the throwaway playbook with `make integration-local TARGET=facts-unbound`: `settings` on `unbound/settings`, key `unbound.general`, `fields: {txtsupport: true}`, check mode, `--diff`; then the real write with apply `unbound/service/reconfigureGeneral`; then `item` add of one host override (`rt-test-one.routerops.test`, `10.250.1.20`) with the Task 3 action names; then `ansible.builtin.uri` GET `unbound/settings/searchHostOverride` and `searchForward`. Record: (a) whether the general write without `active_interface` keeps its stored value (Open question 6 of the research), (b) the apply answers, (c) the search row keys of a host override. Reset the VM; delete the playbook.

### Task 2: Unbound general

**Files:**
- Modify: `meta/areas.yml`, generated files (`make docs`), `docs/testing.md` (verified runs)
- Create: `meta/fields/unbound_general.yml` (`make fields ID=unbound_general`), `tests/integration/test-unbound-general-settings.yml`

- [ ] **Step 1: Catalog entry** `unbound_general`: `area: unbound`, `title: Unbound general`, `module: settings`, values from the API facts tables, `stage: v0`, `tested: ["26.7.7"]`, note: "Every apply restarts Unbound, so DNS stops answering for a moment. A save that changes `enabled` or `port` fails while another service uses the port." Example: "Enable TXT records for host overrides" (`txtsupport: true`).
- [ ] **Step 2: Run** `make fields ID=unbound_general` and `make docs`. Expected: field file with 19 fields, new `docs/areas/unbound.md`; `make docs-check` fails until the test exists.
- [ ] **Step 3: Write the test** after `test-nodeexporter-general-settings.yml`: read the original `txtsupport` in check mode, set the opposite value in check mode (`changed`, no write: a second check-mode read still shows the original), write it, rerun `changed=0`, invalid `port: 70000` -> `validations` naming `unbound.general.port` (no write reaches the router), example twice; `always` restores the original `txtsupport` and asserts a check-mode run with it is `changed=0`.
- [ ] **Step 4: Run** `make integration-reset`, `make integration-local TARGET=test-unbound-general-settings`. Expected: `failed=0`.
- [ ] **Step 5: Fault check:** a copy with a changed value in the rerun must FAIL; a copy whose last assert fails must still leave `txtsupport` restored (query it after the run). Reset the VM.
- [ ] **Step 6:** `make check`; verified-runs row in `docs/testing.md`; commit -> "Add the Unbound general area".

### Task 3: Host override

**Files:** as Task 2 for `unbound_host_override` (`item`), test `test-unbound-host-override-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: Host override`, `key: host`, `lookup: [hostname, domain]`, `actions` from the table, note: "Do not send `aliases`: OPNsense adds and deletes alias items from it; manage them with the host alias area. Deleting a host override also deletes its aliases. Every apply restarts Unbound." Examples: "Add a host override" (`hostname: rt-example`, `domain: routerops.test`, `rr: A`, `server: 10.250.1.30`, `description: routerops example`), "Remove a host override" (`hostname`, `domain`, `state: absent`).
- [ ] **Step 2: Run** `make fields ID=unbound_host_override`, `make docs`.
- [ ] **Step 3: Write the test** in the plan 4b Task 2 pattern: two hosts (`rt-test-one`/`10.250.1.20`, `rt-test-two`/`10.250.1.21`, `rr: A`), check-mode add, add, rerun `changed=0`, check-mode rerun, update `server: 10.250.1.22`, delete, invalid `hostname: "rt-test-one."` -> `validations` naming `host.hostname`, examples twice, cleanup with post-cleanup query.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the Unbound host override area".

### Task 4: Host alias

**Files:** as Task 2 for `unbound_host_alias`, test `test-unbound-host-alias-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: Host alias`, `key: alias`, `lookup: [host, hostname]`, note: "`host` is the uuid of a host override; register it from the host override's outcome. An empty `domain` takes the host's domain." The note adds: "In the examples, replace `EXAMPLE_HOST_UUID` with the `uuid` the host override example returns." Examples: "Add an alias for the example host" (`host: EXAMPLE_HOST_UUID`, `hostname: rt-example-alias`, `description: routerops example`), "Remove the alias" (`host: EXAMPLE_HOST_UUID`, `hostname: rt-example-alias`, `state: absent`). A catalog string stays static: no Jinja in `meta/areas.yml`, because `make docs` and the tests both load it as vars.
- [ ] **Step 2: Run** `make fields ID=unbound_host_alias`, `make docs`.
- [ ] **Step 3: Write the test:** a first block task adds the host `rt-test-one` and the host override example's host (catalog `unbound_host_override`) and registers both uuids; two aliases `rt-test-one-a`, `rt-test-one-b` on `rt-test-one` in the Task 3 pattern; update `description`; invalid `host: 00000000-0000-4000-8000-000000000000` -> `validations` naming `alias.host`; the catalog examples run twice with `items: "{{ item[0]['items'] | to_json | replace('EXAMPLE_HOST_UUID', <example host uuid>) | from_json }}"`. `always`: delete the aliases, the example host and the test host; query all and assert gone.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the Unbound host alias area".

### Task 5: Forward

**Files:** as Task 2 for `unbound_forward`, test `test-unbound-forward-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: Query forward`, `key: dot`, `lookup: [domain, server]`, note: "Forward and DNS over TLS items share one list; the action name sets `type`, so never send it. An empty `domain` forwards every query." Examples: "Forward a domain" (`domain: routerops.test`, `server: 10.250.1.53`, `description: routerops example`), "Remove a forward".
- [ ] **Step 2: Run** `make fields ID=unbound_forward`, `make docs`.
- [ ] **Step 3: Write the test:** two forwards (`one.routerops.test` -> `10.250.1.53`, `two.routerops.test` -> `10.250.1.54`) in the Task 3 pattern; update `port: 5353`; invalid `server: not-an-address` -> `validations` naming `dot.server`; examples twice; cleanup with query.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the Unbound forward area".

### Task 6: ACL

**Files:** as Task 2 for `unbound_acl`, test `test-unbound-acl-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: ACL`, `key: acl`, `lookup: [name]`, note: "Names are not unique; keep them unique, the lookup takes the name." Examples: "Allow a network" (`name: routerops_example`, `action: allow`, `networks: [10.250.72.0/24]`, `description: routerops example`), "Remove an ACL".
- [ ] **Step 2: Run** `make fields ID=unbound_acl`, `make docs`.
- [ ] **Step 3: Write the test:** two ACLs (`rt_test_one` with `[10.250.70.0/24, 10.250.71.0/24]`, `rt_test_two` with `[10.250.71.0/24]`) in the Task 3 pattern; an extra rerun of `rt_test_one` with the networks reversed asserts `changed=0`; update `action: deny`; invalid `networks: [10.250.70.300/24]` -> `validations` naming `acl.networks`; examples twice; cleanup with query.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the Unbound ACL area".

### Task 7: Scenario host override -> host alias

**Files:**
- Create: `tests/integration/scenario-host-override-alias.yml`
- Modify: `docs/testing.md` (verified runs)

- [ ] **Step 1: Write the scenario:** add host `rt-scenario` (`10.250.1.40`), add alias `rt-scenario-alias` on its uuid, rerun both `changed=0`, delete the host only, then query the alias and assert it is gone (OPNsense deleted it with the host). `always`: delete alias and host, query both and assert gone.
- [ ] **Step 2: Run** `make integration-local TARGET=scenario-host-override-alias`. Expected: `failed=0`.
- [ ] **Step 3: Fault check:** a copy that updates the host's `description` instead of deleting it must FAIL on the alias-gone assert. Reset the VM.
- [ ] **Step 4:** `make check`; verified-runs row; commit -> "Add the host override -> alias scenario".

### Task 8: Close plan 4c.1

**Files:** `docs/superpowers/plans/2026-10-17-v0-tracking.md`, `docs/testing.md`

- [ ] **Step 1:** Tracking row 5, facts for `docs/limits.md`: every Unbound apply restarts Unbound; deleting a host override deletes its aliases; Forward and DNS over TLS share one list split by `type`.
- [ ] **Step 2:** `make integration-reset`, then `make integration-local` (all tests and scenarios). Expected: every play `failed=0`. Verified-runs row for the full run.
- [ ] **Step 3:** tracking row 4c.1 -> done; `make check`; commit -> "Close plan 4c.1".
- [ ] **Step 4:** final whole-branch review (most capable model), fix pass, PR.
