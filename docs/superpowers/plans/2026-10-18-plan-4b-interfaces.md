# Plan 4b: VLAN, virtual IP and interface assignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalog entry, field file, integration test and generated page for VLAN, virtual IP and interface assignment (`min_version: "26.7.6"`), plus the VLAN -> assignment -> VIP scenario; `item` gains `id_format: name` for areas whose items are keyed by name instead of UUID.

**Architecture:** One module change (Task 1), then one task per catalog entry following the plan 3 pattern (entry in `meta/areas.yml`, `make fields ID=<id>`, `tests/integration/test-<id>-<module>.yml` reading the entry, `make docs`), one scenario playbook, and a closing task that corrects the spec and module notes the research disproved.

**Tech Stack:** as plan 4a (ansible-core 2.21.5 and 2.20.10, Python 3.12, ansible-test, ansible-lint 26.10.1, yq).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Scope" (v0: Interfaces: VLAN, virtual IP, assignment; assignment needs 26.7.6) and "Module behaviour" (assignment traps). Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`, row 4b. Depends on plan 4a (merged as `be00868`). Facts: research of 18.10.2026 against `opnsense/core` tag 26.7.7, quoted below.

## Global Constraints

- Everything from `AGENTS.md` and plans 3-4a holds: TDD, a new assert counts only after it failed once against a real fault, check mode never writes, a rerun shows `changed=0`, every catalog example runs twice, cleanup in `always` with the post-cleanup query check, every user-visible change gets a fragment.
- Integration runs only against VM 9090 via `make integration-local`; `make integration-reset` before each full run.
- Never touch `wan`, `lan`, `vtnet0` or `vtnet1`'s untagged configuration: VLANs ride on `vtnet1` with tags 4001-4009, assignments only use those VLAN devices, VIPs sit on `lan` (Task 3) or the test VLAN interface (Task 5).
- Catalog ids and test files: `interfaces_vlan`, `interfaces_vip`, `interfaces_assignment`; tests `test-interfaces-vlan-item.yml`, `test-interfaces-vip-item.yml`, `test-interfaces-assignment-item.yml`; scenario `scenario-vlan-assignment-vip.yml`.
- VLAN device names are set explicitly (`vlanif: vlan0.<tag>`), never left to the generator, so an assignment's `if` is known before the run.
- Assignment `descr` matches `^[a-z_0-9]{0,255}$` (no spaces): tests use `rt_test_one`, `rt_test_two`, examples `rt_example`; VLAN and VIP descriptions follow the usual `routerops test` / `routerops example`.
- Test networks: assignment `10.250.40.1/24` (tag 4001) and `10.250.41.1/24` (tag 4002), scenario `10.250.42.1/24` (tag 4003), VIPs on `lan` `10.250.1.240`/`.241`, scenario VIP `10.250.42.10/24`.

### API facts (26.7.7)

| Item | path | key | actions | apply | model file, node | privilege |
|---|---|---|---|---|---|---|
| VLAN | `interfaces/vlan_settings` | `vlan` | `searchItem` `getItem` `addItem` `setItem` `delItem` | `interfaces/vlan_settings/reconfigure` | `Interfaces/Vlan.xml`, `vlan` | `page-interfaces-vlan-edit` "Interfaces: VLAN", `api/interfaces/vlan_settings/*`, Interfaces ACL |
| Virtual IP | `interfaces/vip_settings` | `vip` | same | `interfaces/vip_settings/reconfigure` | `Interfaces/Vip.xml`, `vip` | `page-firewall-virtualipaddress-edit` "Interfaces: Virtual IPs: Settings", `api/interfaces/vip_settings/*`, Interfaces ACL |
| Assignment | `interfaces/assignment` | `interface` | same | `interfaces/assignment/reconfigure` | `Interfaces/NetworkInterface.xml`, `interface` | `page-interfaces-assignnetworkports` "Interfaces: Assign network ports", `api/interfaces/assignment/*`, Core ACL |

Model paths are below `src/opnsense/mvc/app/models/OPNsense/`; ACL files are `<that dir>/Interfaces/ACL/ACL.xml` and `<that dir>/Core/ACL/ACL.xml`. The default action names `search_item` etc. resolve to these, so no `actions` override is needed.

| Fact | Consequence |
|---|---|
| Assignment search rows carry the config key as `uuid` (`wan`, `lan`, `opt1`); `addItem` answers `{"result":"saved","uuid":"optN"}`; interfaces with `<virtual>` and pending deletes are not listed (`NetworkInterface.php:57-65,99-103,169-196`) | Task 1: `id_format: name` makes every row with a non-empty `uuid` an item; the assignment entry sets it; the outcome `uuid` is the interface name a VIP refers to |
| Assignment writes are pending: `setItem`/`addItem`/`delItem` store them in `/tmp/.interfaces.todo`, get and search already return the pending data, `reconfigure` runs `interface apply` over **every** pending entry and answers `{"status":"ok"}` or `{"status":"failed"}` | idempotency holds before the apply; the docs warn that the apply also applies pending changes made in the GUI |
| Assignment `delItem` refuses a locked interface (`lock` defaults to `1`): HTTP 500 "Interface locked, unset lock first before removal"; it does not check VIPs on the interface; `reconfigure` deletes the filter, NAT, outbound, NPT and 1:1 rules on a deleted interface | examples set `lock: false`; cleanup order VIP -> assignment -> VLAN; the docs say a deleted assignment takes its rules with it and leaves its VIPs behind |
| Assignment `descr` is unique with mask `^[a-z_0-9]{0,255}$`; `if` (device) is unique and required; `type4` is `""`/`staticv4`/`dhcp`/`pppoe`/`ppp`; `type6` has no `none` option, `""` means no IPv6; `ipaddr` is CIDR (`10.250.40.1/24`); `staticv4` needs `ipaddr`; `dhcp6-ia-pd-len` is required with no default | lookup `descr` (the search row's `if` may hold the option's description, not the device name; Task 4 checks it live); examples send `type6: ""`; Task 4 checks live whether `dhcp6-ia-pd-len` must be sent |
| Assignment `if` options come from `configd interface list assign-opts`, which lists saved VLANs by `vlanif`; a VLAN needs no `vlan_settings/reconfigure` before it can be assigned | the assignment test adds its VLAN with `item` and the VLAN apply, then assigns it |
| VLAN: `tag` 1-4094, unique with `if`; `pcp` 0-7 default `0`; `vlanif` must match `^vlan0[0-9.]{1,10}$` when sent; search rows show an assigned VLAN's `vlanif` as `vlan0.4001 [DESCR]`, get returns it clean; `delItem` refuses an assigned VLAN: HTTP 500 "This VLAN cannot be deleted because it is assigned as an interface." (checked against `config.interfaces`, so the assignment apply must run before the VLAN delete) | lookup `descr` (not `vlanif`, which the search decorates); scenario asserts the refusal |
| VIP: get returns a pseudo field `network` (`"10.250.1.240/24"`) and drops `subnet`/`subnet_bits`; add and set read `network`; search rows hold `subnet`, `subnet_bits`, `address`, not `network`; `mode` `ipalias`/`carp`/`proxyarp`, default `ipalias`; the address is unique across VIPs; `password` (CARP) is returned in clear; `delItem` refuses a VIP a legacy NAT rule uses (HTTP 500 "Item in use by") | fields send `network`; lookup `descr` (the only lookup present in both search and get); `secret_fields: [password]`; the area note explains `network` |
| VLAN and VIP search rows are all MVC items with UUIDs | `id_format` stays `uuid` for both |

## Review Focus

- `purge: true` with `id_format: name` on the assignment area would delete `wan` and `lan`: expect the module to fail before any request (Task 1).
- An assignment rerun before any apply (pending data only): expect `changed=0`, because get returns the pending values (Task 4 rerun assert).
- Assignment cleanup aborted after the assignment delete but before its apply: expect the VLAN delete in `always` to fail loudly, not pass silently; the `always` block applies the assignment before deleting the VLAN (Task 4, Task 5).
- A VIP lookup by `descr` that equals an existing VIP's on another interface: expect an update of that VIP, documented in the area note as the reason descriptions must be unique (Task 3 note).
- A VLAN whose search row shows `vlan0.4001 [rt_test_one]` after assignment: expect the VLAN rerun to stay `changed=0`, since the lookup is `descr` and the compare reads get (Task 5 rerun assert).

## Owner step before Task 2

Give the API user `ansible-test` on VM 9090 the three privileges from the table above (in addition to the ones it has), shut the VM down, delete the snapshot `clean` and take it again. The agent cannot do this: the test user has no `auth/user` privilege, and the snapshot lives on the owner's Proxmox.

---

### Task 1: `item` option `id_format`

**Files:**
- Modify: `plugins/modules/item.py` (`DOCUMENTATION`, `ARGUMENT_SPEC`, `Run.__init__`, `mvc_rows`, `run`, `section`, `check_options`)
- Test: `tests/unit/plugins/modules/test_item.py`
- Create: `changelogs/fragments/item-id-format.yml` (`minor_changes`)

**Interfaces:**
- Produces: option `id_format` (`str`, choices `[uuid, name]`, default `uuid`, `version_added: "0.1.0"`); `Run.is_item(row) -> bool` (with `uuid`: `MVC_UUID` match as today; with `name`: `row["uuid"]` is a non-empty string); `mvc_rows` and the `other_rows` filter in `run` use `is_item` (`mvc_rows` becomes an instance method; rename it `item_rows`).

- [ ] **Step 1: Write the failing tests**: `test_id_format_name_matches_name_rows` (rows `{"uuid": "lan", "descr": "LAN", ...}`, `{"uuid": "opt1", "descr": "rt_test_one", ...}`; lookup `descr`, wanted `rt_test_one` with a changed field; expect `setItem/opt1` sent, outcome `updated`, `uuid == "opt1"`), `test_id_format_name_add_returns_name` (add response `{"result": "saved", "uuid": "opt2"}`; outcome `uuid == "opt2"`), `test_id_format_name_rejects_purge` (`purge: true`; expect failure `"purge cannot be combined with id_format name"` and no request sent), `test_id_format_uuid_still_ignores_name_rows` (default; a `uuid: "opt1"` row with the wanted `descr` -> `addItem` sent).
- [ ] **Step 2: Run** `make units`. Expected: the first three FAIL (unknown option `id_format`), the fourth PASS (pins behaviour).
- [ ] **Step 3: Implement.** `check_options` fails on `purge` with `id_format: name` before the search. `section`'s "is not an MVC item" message applies only to `id_format: uuid`. Docs: `id_format` description "How the search names its items. V(uuid) takes only rows whose C(uuid) is a UUID. V(name) takes every row and suits areas keyed by name, such as interface assignment (C(lan), C(opt1))." plus "O(purge) cannot be combined with V(name)."; the note "Interface assignment items are keyed by the interface name, not a UUID, and are looked up by their device field." becomes "Interface assignment items are keyed by the interface name, not a UUID; set O(id_format=name)." (Task 6 corrects the lookup part if Task 4 shows otherwise).
- [ ] **Step 4: Run** `make units` and `make check`. Expected: PASS.
- [ ] **Step 5: Commit** with the fragment -> "Add id_format for items keyed by name".

### Task 2: VLAN

**Files:**
- Modify: `meta/areas.yml`, generated files (`make docs`)
- Create: `meta/fields/interfaces_vlan.yml` (`make fields ID=interfaces_vlan`), `tests/integration/test-interfaces-vlan-item.yml`

- [ ] **Step 1: Catalog entry** `interfaces_vlan`: `area: interfaces`, `title: VLAN`, values from the API facts table, `lookup: [descr]`, `stage: v0`, `tested: ["26.7.7"]`, note: "Set `vlanif` (`vlan0.<tag>`) so the device name is known before the VLAN is assigned; OPNsense refuses to delete a VLAN that is assigned as an interface." Examples: "Add a VLAN on the LAN port" (`if: vtnet1`, `tag: 4009`, `vlanif: vlan0.4009`, `descr: routerops example`), "Remove a VLAN" (`descr: routerops example`, `state: absent`).
- [ ] **Step 2: Run** `make fields ID=interfaces_vlan` and `make docs`. Expected: field file, `docs/areas/interfaces.md` with the section; `make docs-check` fails until the test exists.
- [ ] **Step 3: Write the test** after `test-routing-gateway-item.yml`: two VLANs (tags 4001, 4002 on `vtnet1`, `vlanif: vlan0.4001`/`vlan0.4002`, `routerops test one`/`two`), check-mode add, add, rerun `changed=0`, check-mode rerun, update `pcp: 3`, delete, invalid (`tag: 4095` -> `validations`), examples twice, cleanup with post-cleanup query.
- [ ] **Step 4: Run** `make integration-reset` then `make integration-local TARGET=test-interfaces-vlan-item`. Expected: `failed=0`.
- [ ] **Step 5: Fault check:** a copy with a changed wanted value in the idempotency task must FAIL. Reset the VM.
- [ ] **Step 6:** `make check`; verified-runs row in `docs/testing.md`; commit -> "Add the VLAN area".

### Task 3: Virtual IP

**Files:** as Task 2 for `interfaces_vip`, test `test-interfaces-vip-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: Virtual IP`, `lookup: [descr]`, `secret_fields: [password]` (existing catalog key; the test passes it as `test-firewall-alias-item.yml` does), note: "OPNsense reads and returns the address as `network` (`10.250.1.240/24`), not as `subnet` and `subnet_bits`. Descriptions identify a VIP; keep them unique. A CARP `password` is returned in clear, so name it in `secret_fields`." Examples: "Add an IP alias on LAN" (`mode: ipalias`, `interface: lan`, `network: 10.250.1.250/24`, `descr: routerops example`), "Remove a virtual IP".
- [ ] **Step 2: Run** `make fields ID=interfaces_vip`, `make docs`.
- [ ] **Step 3: Write the test:** two IP aliases on `lan` (`10.250.1.240/24`, `10.250.1.241/24`), Task 2 pattern; update `network` to `10.250.1.242/24` and assert the rerun is `changed=0`; invalid: `network: 10.250.1.255/24` (broadcast) -> `validations` naming `vip.network`.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the virtual IP area".

### Task 4: Interface assignment

**Files:** as Task 2 for `interfaces_assignment`, test `test-interfaces-assignment-item.yml`; `meta/areas.yml` gains `id_format` as an optional catalog key passed to the module (add it to `generate-docs.yml`'s argument spec next to `secret_fields`, `type: str`, choices `[uuid, name]`; `tools/templates/example.yml.j2` emits it like `secret_fields`; the test passes `opnsense_test_area['id_format'] | default('uuid')`).

- [ ] **Step 1: Live facts first.** On the reset VM, with the VLAN entry from Task 2, add VLAN `vlan0.4001` and then run `item` against `interfaces/assignment` once with `id_format: name`, `lookup: [descr]`, `state: query` for `descr: LAN` and `return_fields: [if, type6]`; then add `rt_test_one` (`if: vlan0.4001`, `enable: true`, `lock: false`, `type4: staticv4`, `ipaddr: 10.250.40.1/24`, `type6: ""`) without `dhcp6-ia-pd-len`. Record in the task commit message: (a) the search row's `if` value for `lan` (device name or description), (b) whether the add needs `dhcp6-ia-pd-len` (validation names it) and which value get returns, (c) `type6` as read for `lan`. Reset the VM.
- [ ] **Step 2: Catalog entry:** `title: Assignment`, `id_format: name`, `lookup: [descr]` (switch to `[if]` only if (a) showed the device name and the spec wants it; record the choice), `min_version: "26.7.6"`, note: "Items are keyed by the interface name (`opt1`); the outcome `uuid` is that name, which a virtual IP takes as `interface`. The apply runs `interface apply` for every pending interface change, including ones made in the GUI, and can cut the management connection when it touches the interface you connect through. Set `lock: false`, or OPNsense refuses the delete. A deleted assignment takes its firewall and NAT rules with it and leaves its virtual IPs behind; delete those first. `type6: \"\"` means no IPv6." Examples: "Assign a VLAN with a static address" (fields as Step 1 with `vlan0.4009`, `ipaddr: 10.250.49.1/24`, `descr: rt_example`, plus `dhcp6-ia-pd-len` if (b) requires it), "Remove an assignment". The example page states that the VLAN example above must run first.
- [ ] **Step 3: Run** `make fields ID=interfaces_assignment`, `make docs`. Expected: `docs/areas/interfaces.md` shows "Minimum OPNsense 26.7.6".
- [ ] **Step 4: Write the test:** a first block task adds VLANs 4001, 4002 and 4009 (catalog `interfaces_vlan`); then two assignments `rt_test_one` (`vlan0.4001`, `10.250.40.1/24`), `rt_test_two` (`vlan0.4002`, `10.250.41.1/24`) in the Task 2 pattern; extra asserts: every outcome `uuid` matches `^opt[0-9]+$`, the rerun before and after the apply is `changed=0`; update `ipaddr` to `10.250.40.2/24`; invalid: `type4: staticv4` without `ipaddr` (field `ipaddr: ""`) -> `validations` naming `interface.ipaddr`. `always`: delete the assignments (the module applies), then the VLANs, then query both and assert gone.
- [ ] **Step 5: Run** `make integration-reset`, `make integration-local TARGET=test-interfaces-assignment-item`. Expected: `failed=0`; the tunnel stays up (LAN untouched).
- [ ] **Step 6: Fault check:** a copy run against a collection built from `main` (no `id_format`) must FAIL (the rerun adds a duplicate or the add fails on the unique `if`); a copy with a changed idempotency value must FAIL. Reset the VM.
- [ ] **Step 7:** `make check`, verified-runs row with the Step 1 observations, commit -> "Add the interface assignment area".

### Task 5: Scenario VLAN -> assignment -> VIP

**Files:**
- Create: `tests/integration/scenario-vlan-assignment-vip.yml`
- Modify: `docs/testing.md` (verified runs)

- [ ] **Step 1: Write the scenario:** add VLAN `vlan0.4003` (`routerops test scenario`), assign it as `rt_scenario` with `10.250.42.1/24` and register the outcome `uuid`, add VIP `10.250.42.10/24` with `interface` set to that `uuid`; rerun all three `changed=0` (the VLAN rerun proves the decorated search row does not break the lookup); try to delete the VLAN (`ignore_errors`), assert `failed`, `not changed` and `'assigned as an interface' in msg`. `always`: delete the VIP, then the assignment, then the VLAN, then query all three and assert gone.
- [ ] **Step 2: Run** `make integration-local TARGET=scenario-vlan-assignment-vip`. Expected: `failed=0` (one ignored expected failure).
- [ ] **Step 3: Fault check:** a copy that deletes the VLAN after the assignment cleanup instead of while assigned must FAIL on the `failed` assert. Reset the VM.
- [ ] **Step 4:** `make check`; verified-runs row; commit -> "Add the VLAN -> assignment -> VIP scenario".

### Task 6: Close plan 4b

**Files:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, `plugins/modules/item.py` (`notes`), `docs/superpowers/plans/2026-10-17-v0-tracking.md`, `docs/testing.md`

- [ ] **Step 1: Correct what the research disproved.** Spec "Module behaviour" traps and the `item` note: "`type6` must be `none`, not `\"\"`" becomes "`type6` takes `\"\"` for no IPv6; there is no `none`" (confirm with Task 4 Step 1 (c) first); "looked up by their device field" becomes the lookup Task 4 chose, with `id_format: name`. Tracking row 5, facts for `docs/limits.md`: the assignment apply applies every pending interface change, also GUI ones; deleting an assignment leaves its VIPs and deletes its rules; a VIP's CARP password is readable through the API.
- [ ] **Step 2:** `make integration-reset`, then `make integration-local` (all tests and both scenarios). Expected: every play `failed=0`. Verified-runs row for the full run.
- [ ] **Step 3:** tracking row 4b -> done, file name `2026-10-18-plan-4b-interfaces.md`; `make check`; commit -> "Close plan 4b".
- [ ] **Step 4:** final whole-branch review (most capable model), fix pass, PR.
