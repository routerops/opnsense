# Plan 4d.2: WireGuard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalog entry, field file, integration test and generated section for WireGuard server (instance) and peer, plus the server -> peer scenario.

**Architecture:** No module change: plan 4d.1 Task 1 made `require_ok` accept `{"result":"ok"}`, which `wireguard/service/reconfigure` answers. The peer entry is the second to use `always_send` (plan 4c.3): OPNsense drops a peer from every server when a write leaves out `servers`. The plan 4c.1 pattern per catalog entry, one scenario and a closing task.

**Tech Stack:** as plan 4b.

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Scope" (v0: WireGuard server, peer) and "Module behaviour" (`secret_fields` for `privkey` and `psk`, `ordered_fields` for the peer `tunneladdress`). Tracking: row 4d. Depends on plan 4d.1 (`2026-10-18-plan-4d1-trust-openvpn.md`). Followed by plan 4d.3 (`2026-10-18-plan-4d3-ipsec.md`). Facts: research of 18.10.2026 against `opnsense/core` tag 26.7.7.

## Global Constraints

- Everything from plan 4d.1's Global Constraints holds, except its test data.
- WireGuard stays disabled (`wireguard.general.enabled` 0): no test enables it, so no `wg` interface comes up on the VM. The apply still runs and answers `ok`.
- Keys come from `wireguard/server/key_pair` (`GET`, answers `privkey`, `pubkey`, `status`), registered with `no_log: true`. Examples use the placeholders `EXAMPLE_SERVER_PRIVKEY`, `EXAMPLE_SERVER_PUBKEY`, `EXAMPLE_PEER_PUBKEY`, `EXAMPLE_SERVER_UUID`, which the tests replace.
- Test data is invented: servers `rt-test-one`, `rt-test-two`, example `rt-example`; ports `51820`, `51821`, example `51822`; server tunnel addresses `10.250.90.1/24`, `10.250.91.1/24`, example `10.250.92.1/24`; peers `rt-test-peer-one`, `rt-test-peer-two`, example `rt-example-peer`, tunnel addresses `10.250.90.2/32`, `10.250.90.3/32`, example `10.250.92.2/32`.
- Catalog ids and test files: `wireguard_server`, `wireguard_peer`; tests `test-wireguard-server-item.yml`, `test-wireguard-peer-item.yml`; scenario `scenario-wireguard-server-peer.yml`.

### API facts (26.7.7)

Both entries: apply `wireguard/service/reconfigure`, privilege `page-wireguard-config` "VPN: WireGuard: Configuration", patterns `api/wireguard/server/*`, `api/wireguard/client/*`, `api/wireguard/general/*`, `api/wireguard/service/*` (`Wireguard/ACL/ACL.xml:2-11`).

| Item | path | key | actions | model, node |
|---|---|---|---|---|
| Server | `wireguard/server` | `server` | `searchServer` `getServer` `addServer` `setServer` `delServer` | `Wireguard/Server.xml`, `servers.server` |
| Peer | `wireguard/client` | `client` | `searchClient` `getClient` `addClient` `setClient` `delClient` | `Wireguard/Client.xml`, `clients.client` |

| Fact | Consequence |
|---|---|
| Apply answers `{"result":"ok"}` always, also while WireGuard is disabled; it runs `wireguard configure`, which with WireGuard disabled renders nothing and removes every `wg` interface (ServiceController.php:51-63, wg-service-control.php:221,324-333) | relies on plan 4d.1 Task 1; the notes say the apply does not report a failed configure and that WireGuard runs only after `wireguard/general` `enabled` is set |
| Server: `name` required (mask `^[0-9a-zA-Z._\-]{1,64}$`), `instance` auto-numbered, `privkey` required, `pubkey` optional and never derived from `privkey`, `tunneladdress` list (CIDR), `port`, `disableroutes`; `gateway` needs `disableroutes: true`; no unique constraint (Server.xml:8-80) | lookup `[name]`; never send `instance`; examples send `privkey` and `pubkey` from one key pair |
| Server `peers` is the stored relation; peer `servers` is volatile and filled from it (Client.xml:59, ClientField.php:39-58) | never send server `peers`; manage the relation through the peer's `servers` |
| `setClient` and `addClient` read `client.servers` as a comma-separated string before the write; missing or empty, the peer is removed from every server's `peers` (ClientController.php:99-134) | `always_send: [servers]`; the note says so |
| `delClient` first removes the peer from every server's `peers`; `delServer` has no cleanup (ClientController.php:83-97, ServerController.php:60-63) | the scenario asserts the server's `peers` is empty after the peer is deleted |
| Peer: `name` required, `pubkey` required (base64 round trip only, "Invalid Base64-encoded string."), `pubkey` + `serveraddress` + `serverport` unique, `tunneladdress` required list kept in the sent order, `keepalive` 1-65535 (0 rejected) (Client.xml:8-70, BaseSetField.php:82-114) | lookup `[name]`; `ordered_fields: [tunneladdress]`; invalid cases `keepalive: 0` and a bad `pubkey` |
| Server `privkey`, peer `privkey` and `psk` are returned by get and in every search row | server `secret_fields: [privkey]`, peer `secret_fields: [psk]`; the notes say the keys are readable through the API |

## Review Focus

- A peer update that changes only `description`: expect the peer to stay attached to its server, because `servers` goes along through `always_send` (Task 4 fault check without `always_send` must lose the relation).
- A peer `tunneladdress` sent in another order than stored: expect a change, because the field keeps its order (Task 3 asserts it; Task 1 confirms the stored order first).
- A server rerun that leaves out `peers`: expect `changed=0`, because `peers` is not compared (Task 4 reruns the server after the peer is attached).
- A server sent with `privkey` only: expect `pubkey` to stay empty; the note says to send both (no test: documented input).
- A peer whose server was deleted in the GUI: expect the add to fail on `client.servers`, never to attach to another server (Task 3 invalid case with an unknown uuid).

---

### Task 1: Live facts

**Files:** none committed; a throwaway `tests/integration/facts-wireguard.yml`, deleted after the step.

- [ ] **Step 1:** After `make integration-reset`: GET `wireguard/server/key_pair` twice; add server `rt-facts` with one pair; add peer `rt-facts-peer` (`pubkey` of the second pair, `tunneladdress: [10.250.90.3/32, 10.250.90.2/32]`, `servers: [<server uuid>]`); GET the peer and record the `tunneladdress` key order and the shape of `servers`; POST `setClient/<uuid>` with only `description` and record whether the server's `peers` lost the peer; POST `wireguard/service/reconfigure` and record the answer. Reset the VM; delete the playbook.
- [ ] **Step 2:** If the stored order differs from the sent order, drop `ordered_fields` from Task 3, record the fact for the spec ("WireGuard peer `tunneladdress` keeps its order" becomes wrong) and tell the owner.

### Task 2: WireGuard server

**Files:**
- Modify: `meta/areas.yml`, generated files (`make docs`), `docs/testing.md`
- Create: `meta/fields/wireguard_server.yml`, `tests/integration/test-wireguard-server-item.yml`

- [ ] **Step 1: Catalog entry** `wireguard_server`: `area: wireguard`, `title: WireGuard server`, `module: item`, values from the tables, `lookup: [name]`, `secret_fields: [privkey]`, `stage: v0`, `tested: ["26.7.7"]`; note: "Create the key pair with `wireguard/server/key_pair` and send `privkey` and `pubkey`; OPNsense does not derive the public key. Attach peers through the peer's `servers`, never through `peers`. OPNsense numbers servers itself (`instance`, interface `wgN`). WireGuard runs only after `wireguard/general` `enabled` is set; the apply answers `ok` even when the configuration fails. The private key is readable through the API. Names identify a server; keep them unique." The note adds: "In the examples, replace `EXAMPLE_SERVER_PRIVKEY` and `EXAMPLE_SERVER_PUBKEY` with a generated key pair." Examples: "Add a WireGuard server" (`name: rt-example`, `privkey: EXAMPLE_SERVER_PRIVKEY`, `pubkey: EXAMPLE_SERVER_PUBKEY`, `port: "51822"`, `tunneladdress: [10.250.92.1/24]`), "Remove a WireGuard server" (`name`, `state: absent`).
- [ ] **Step 2: Run** `make fields ID=wireguard_server`, `make docs`.
- [ ] **Step 3: Write the test** in the plan 4c.1 Task 3 pattern: three key pairs (`no_log: true`); servers `rt-test-one` and `rt-test-two` from the Global Constraints; the add diff never holds the private key (assert); update `mtu: "1400"`; invalid `tunneladdress: [10.250.90.1]` (no mask) -> `validations` naming `server.tunneladdress`; examples twice with the placeholders replaced; cleanup with query.
- [ ] **Step 4: Run** `make integration-reset`, `make integration-local TARGET=test-wireguard-server-item`. Expected: `failed=0`.
- [ ] **Step 5: Fault check:** a copy without `secret_fields` must FAIL the diff assert; a copy with a changed idempotency value must FAIL. Reset the VM.
- [ ] **Step 6:** `make check`, verified-runs row, commit -> "Add the WireGuard server area".

### Task 3: WireGuard peer

**Files:** as Task 2 for `wireguard_peer`, test `test-wireguard-peer-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: WireGuard peer`, `key: client`, `lookup: [name]`, `secret_fields: [psk]`, `ordered_fields: [tunneladdress]`, `always_send: [servers]`; note: "`servers` lists the uuids of the servers the peer belongs to. OPNsense reads it on every write and drops the peer from every server when it is missing, so the module always sends it; list it in every present item. `keepalive` takes 1 to 65535; leave it out for none. The pre-shared key is readable through the API." The note adds: "In the examples, replace `EXAMPLE_PEER_PUBKEY` with the peer's public key and `EXAMPLE_SERVER_UUID` with the `uuid` the server example returns." Examples: "Add a WireGuard peer" (`name: rt-example-peer`, `pubkey: EXAMPLE_PEER_PUBKEY`, `tunneladdress: [10.250.92.2/32]`, `servers: [EXAMPLE_SERVER_UUID]`), "Remove a WireGuard peer" (`name`, `state: absent`; `always_send` binds only present items).
- [ ] **Step 2: Run** `make fields ID=wireguard_peer`, `make docs`.
- [ ] **Step 3: Write the test:** a first block task adds server `rt-test-one` and the example server and registers both uuids; peers `rt-test-peer-one` (`10.250.90.2/32`) and `rt-test-peer-two` (`[10.250.90.3/32, 10.250.90.4/32]`) on `rt-test-one` in the plan 4c.1 Task 3 pattern; an extra run of `rt-test-peer-two` with the addresses reversed asserts `changed`; update `keepalive: 25`; invalid cases `keepalive: 0` -> `validations` naming `client.keepalive`, `pubkey: "not base64!"` -> `client.pubkey`, `servers: [00000000-0000-4000-8000-000000000000]` -> `failed` and `not changed`; examples twice with the placeholders replaced; `always`: peers, then servers; query all and assert gone.
- [ ] **Step 4-6:** run, fault check (idempotency; a copy without `ordered_fields` must FAIL the reversed-order assert), `make check`, verified-runs row, commit -> "Add the WireGuard peer area".

### Task 4: Scenario server -> peer

**Files:**
- Create: `tests/integration/scenario-wireguard-server-peer.yml`
- Modify: `docs/testing.md`

- [ ] **Step 1: Write the scenario:** add server `rt-scenario` (`10.250.93.1/24`), add peer `rt-scenario-peer` with `servers: [<server uuid>]`; rerun both `changed=0`; update the peer's `description` only; GET `wireguard/server/getServer/<uuid>` through `ansible.builtin.uri` and assert the peer uuid is selected in `server.peers` (`return_fields` cannot read a multi-select); delete the peer and assert `server.peers` has nothing selected. `always`: peer, then server; query both and assert gone.
- [ ] **Step 2: Run** `make integration-local TARGET=scenario-wireguard-server-peer`. Expected: `failed=0`.
- [ ] **Step 3: Fault check:** a copy whose peer update passes `always_send: []` must FAIL the "peer still selected" assert. Reset the VM.
- [ ] **Step 4:** `make check`; verified-runs row; commit -> "Add the WireGuard server -> peer scenario".

### Task 5: Close plan 4d.2

**Files:** `docs/superpowers/plans/2026-10-17-v0-tracking.md`, `docs/testing.md`, `changelogs/fragments/areas-vpn.yml`

- [ ] **Step 1:** Fragment: add "WireGuard (server, peer)" to the plan 4d.1 sentence.
- [ ] **Step 2:** Tracking row 5, facts for `docs/limits.md`: the WireGuard apply answers `ok` without checking the configure; a peer write without `servers` detaches it (the module sends it); WireGuard keys are readable through the API.
- [ ] **Step 3:** `make integration-reset`, `make integration-local` (everything). Expected: every play `failed=0`. Verified-runs row.
- [ ] **Step 4:** tracking row 4d.2 -> done; `make check`; commit -> "Close plan 4d.2".
