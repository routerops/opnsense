# Plan 4d.1: Trust and OpenVPN Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Catalog entry, field file, integration test and generated section for Trust CA and certificate, OpenVPN instance, static key and client-specific override, plus the CA -> certificate -> OpenVPN instance scenario; actions that answer `result: ok` count as applied; catalog examples carry `write_only` values.

**Architecture:** Two code changes first: `require_ok` in `plugins/module_utils/_client.py` accepts `{"result": "ok"}` when the answer has no `status` (OpenVPN and WireGuard apply answer that way), and catalog example items gain `write_only` (Trust create inputs are volatile). Then the plan 4c.1 pattern per catalog entry, one scenario and a closing task.

**Tech Stack:** as plan 4b (ansible-core 2.21.5 and 2.20.10, Python 3.12, ansible-test, ansible-lint 26.10.1, yq).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Scope" (v0: OpenVPN instance, static key, client-specific override; Trust CA and certificate as far as the OpenVPN tests need them) and "Module behaviour" (`write_only` for the volatile Trust create inputs, `return_fields` for a `refid`). Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`, row 4d. Depends on plan 4c (closed in `e1a8c43`). Followed by plan 4d.2 (`2026-10-18-plan-4d2-wireguard.md`) and 4d.3 (`2026-10-18-plan-4d3-ipsec.md`). Facts: research of 18.10.2026 against `opnsense/core` tag 26.7.7, quoted below.

## Global Constraints

- Everything from plan 4c.1's Global Constraints holds, except the Unbound-specific lines.
- Test data is invented: CA `routerops test ca` (common name `routerops-test-ca`), certificates `routerops test server` / `routerops test two` (common names `rt-test-server`, `rt-test-two`), example CA `routerops example ca`, example certificate `routerops example server`; OpenVPN tunnel networks `10.250.80.0/24`, `10.250.81.0/24`, example `10.250.82.0/24`; ports `11940`, `11941`, example `11942`; CSO common names `rt-test-client-one`, `rt-test-client-two`, example `rt-example-client`; descriptions `routerops test one` / `two`, examples `routerops example`.
- Catalog ids and test files: `trust_ca`, `trust_cert`, `openvpn_instance`, `openvpn_static_key`, `openvpn_cso`; tests `test-trust-ca-item.yml`, `test-trust-cert-item.yml`, `test-openvpn-instance-item.yml`, `test-openvpn-static-key-item.yml`, `test-openvpn-cso-item.yml`; scenario `scenario-ca-cert-openvpn.yml`.
- Secrets in examples start with `EXAMPLE` (AGENTS.md); a test replaces such a placeholder with a value it generates on the router (plan 4c.1 Task 4 pattern with `replace`).

### API facts (26.7.7)

| Item | path | key | actions | apply | model, node | privilege |
|---|---|---|---|---|---|---|
| CA | `trust/ca` | `ca` | `search` `get` `add` `set` `del` | none (add, set and del run `system trust configure` inline) | `Trust/Ca.xml`, `ca` | `page-system-camanager` "System: Trust: Authorities", `api/trust/ca/*` |
| Certificate | `trust/cert` | `cert` | `search` `get` `add` `set` `del` | none | `Trust/Cert.xml`, `cert` | `page-system-certmanager` "System: Trust: Certificates", `api/trust/cert/*` |
| Instance | `openvpn/instances` | `instance` | `search` `get` `add` `set` `del` | `openvpn/service/reconfigure` | `OpenVPN/OpenVPN.xml`, `Instances.Instance` | `page-openvpn-instances` "VPN: OpenVPN: Instances", `api/openvpn/instances/*`, and `page-status-openvpn` "Status: OpenVPN", `api/openvpn/service/*` |
| Static key | `openvpn/instances` | `statickey` | `searchStaticKey` `getStaticKey` `addStaticKey` `setStaticKey` `delStaticKey` | `openvpn/service/reconfigure` | as instance, `StaticKeys.StaticKey` | as instance |
| CSO | `openvpn/client_overwrites` | `cso` | `search` `get` `add` `set` `del` | none (read when a client connects, `client_connect.php:41`) | as instance, `Overwrites.Overwrite` | `page-openvpn-csc` "VPN: OpenVPN: Client Specific Override", `api/openvpn/client_overwrites/*` |

Privileges from `src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml:357-363,458-471,569-582`.

| Fact | Consequence |
|---|---|
| `openvpn/service/reconfigure` answers `{"result":"ok"}`, `{"result":"failed"}` for a non-POST (ServiceController.php:244-254); `wireguard/service/reconfigure` the same (plan 4d.2); `require_ok` reads only `status` (`_client.py:147-152`) | Task 1: accept `result: ok` when there is no `status`; spec "Module behaviour" and the AGENTS.md "API results" row name both shapes |
| CA and certificate create inputs are volatile and never stored: CA `action` (default `internal`), `key_type`, `digest`, `lifetime`, `commonname`, `country` (default `NL`), `city`, `state`, `organization`, `organizationalunit`, `email`; certificate also `cert_type` (default `usr_cert`), `private_key_location`, `altnames_dns` (newline-separated), `altnames_ip`, `altnames_uri`, `altnames_email` (Ca.xml:21-90, Cert.xml:21-127, BaseField.php:869-873) | these go in `write_only`; only `descr` and `caref` are compared; Task 2 lets catalog examples carry `write_only` |
| `get` and search return the volatile fields with values parsed from the stored certificate (`commonname`, `key_type`, `digest`, `cert_type`, ...), `action` forced to `existing` (CA) or derived `reissue`/`manual` (certificate); `prv` and `prv_payload` (the private key) are in get and in every search row (CAsField.php:85-122, CertificatesField.php:147-201) | never compare the volatile fields; the notes say the private key is readable through the API |
| `refid` is generated by `uniqid()` when empty and returned by search and get; no uniqueness check (CaController.php:57-59, CertController.php:54-56) | `return_fields: [refid]`; lookup `[descr]`, the notes ask for unique descriptions |
| A `set` on a certificate that holds its key reissues it (derived `action: reissue`, CertController.php:149-165); a CA `set` re-imports without regenerating (CaController.php:102-108) | the certificate note says every update reissues the certificate with the same key; the test updates `descr` once and asserts the rerun is `changed=0` |
| A certificate signed by a CA: `caref` = the CA `refid`; a bad `caref` -> `cert.caref` "Please select a valid certificate from the list." (CertificateField.php:48-51) | invalid case of the certificate test |
| CA delete is never refused, even while certificates or instances use it (`internalModelUseSafeDelete` false, CaController.php:169-174); certificate delete in use -> `UserException` "Item in use by", HTTP 500 (CertController.php:213, `api.php:48-49`) | the CA note warns; the scenario asserts the certificate delete fails while the instance uses it |
| Certificate search lists external certificates whose uuid is not a UUID (CertificatesField.php:117-132) | `item` skips them (plan 2); no purge example |
| Instance: `role` default `server`, `dev_type` `tun`, `proto` `udp`, `topology` `subnet`, `verify_client_cert` `require`, `vpnid` auto-assigned and unique, `cert` and `ca` are refids, `tls_key` the uuid of a static key, `description` optional; a tun server needs `server` (IPv4 CIDR, /29 or shorter) or `server_ipv6`; `cert` required while `verify_client_cert` is not `none` (OpenVPN.xml:83-375, OpenVPN.php:75-181) | lookup `[description]`; never send `vpnid`; examples send `role`, `dev_type`, `proto`, `port`, `server`, `cert`, `description` |
| Instance bad cert -> `instance.cert` "Please select a valid certificate from the list."; no tunnel network -> `instance.server` "At least one IPv4 or IPv6 tunnel network is required." | invalid case of the instance test |
| Instance `password` and `auth-gen-token-secret` are plain fields returned by get (OpenVPN.xml:353-375) | the instance entry names `password` in `secret_fields` |
| Static key: `mode` (default `crypt`), `key` required (mask `^([0-9a-z#\-=+/\r\n\s])*$`i), `description` required; `key` returned by get in clear; search rows hold only `description`; `openvpn/instances/gen_key/<type>` (`tls-auth`, `tls-crypt`, `tls-crypt-v2-server`) answers `{"result":"ok","key":...}` (OpenVPN.xml:437-455, InstancesController.php:78-112) | lookup `[description]`, `secret_fields: [key]`; the test generates the key with `gen_key/tls-crypt` |
| Instance and static key delete are never refused, also while an instance uses the key | the static key note warns |
| CSO: `common_name` required, `servers` multiple (legacy vpnids and MVC instance uuids; empty = every server), `tunnel_network` IPv4 CIDR; no unique constraint (OpenVPN.xml:6-80, OpenVPNServerField.php:41-63) | lookup `[common_name]` |
| Every `UserException` (Trust certificate errors, in-use) answers HTTP 500 with `errorTitle`/`errorMessage` | `_client.py` shows it (plan 3c); invalid cases use validations only |

## Review Focus

- A certificate rerun with the same `descr` and `write_only` values: expect `changed=0` and no reissue, because volatile fields are never compared and `update_write_only` stays `on_create` (Task 4 rerun asserts the certificate `crt` is unchanged through a GET before and after).
- An apply answering `{"status": "ok", "result": "failed"}`: expect `status` to decide, so the action counts as applied (Task 1 unit test).
- An apply answering `{"result": "failed"}`: expect the task to fail with the result in the message (Task 1 unit test).
- Deleting a CA that a certificate uses: expect OPNsense to delete it and the certificate to stay; the scenario asserts the order certificate -> CA in its cleanup so no orphan stays (Task 8 cleanup order).
- An instance update that changes only `description`: expect the rerun `changed=0` though `get` returns `vpnid`, `cert` and other fields not sent (Task 5 rerun).

## Owner step before Task 3

Give the API user `ansible-test` on VM 9090 the privileges `page-system-camanager`, `page-system-certmanager`, `page-openvpn-instances`, `page-status-openvpn`, `page-openvpn-csc` (plan 4d.1), `page-wireguard-config` (plan 4d.2), `page-vpn-ipsec-connections` and `page-vpn-ipsec-editkeys` (plan 4d.3), shut the VM down, delete the snapshot `clean` and take it again.

---

### Task 1: Accept `result: ok` from an action

**Files:**
- Modify: `plugins/module_utils/_client.py:147-152` (`require_ok`), `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md` (line 73, success rule), `AGENTS.md` ("API results" row)
- Test: `tests/unit/plugins/module_utils/test_client.py`
- Create: `changelogs/fragments/apply-result-ok.yml`

**Interfaces:**
- Produces: `require_ok(response)` passes on `status` equal to `ok` (trimmed, any case); when the response has no `status` key, it passes on `result` equal to `ok` (trimmed, any case); otherwise it raises `OPNsenseError("action failed: <status or result> <status_msg>")`.

- [ ] **Step 1: Write the failing tests:** `test_require_ok_accepts_result_ok` (`{"result": "ok"}`, `{"result": " OK"}` pass); `test_require_ok_status_wins_over_result` (`{"status": "ok", "result": "failed"}` passes, `{"status": "failed", "result": "ok"}` raises); `test_require_ok_raises_on_result_failed` (`{"result": "failed"}` raises, `"failed"` in `e.value.msg`).
- [ ] **Step 2: Run** `make units`. Expected: FAIL on the first and third test.
- [ ] **Step 3: Implement** in `require_ok`: take `status` if the key exists, else `result`; message names that value.
- [ ] **Step 4: Run** `make units`. Expected: PASS.
- [ ] **Step 5:** spec line 73 and the AGENTS.md row: "an action on `status` `ok`, or on `result` `ok` when the answer has no `status` (OpenVPN, WireGuard)". Fragment `minor_changes`: "item, settings - an apply that answers ``result: ok`` without ``status``, as OpenVPN and WireGuard do, counts as applied."
- [ ] **Step 6:** `make check`; commit -> "Accept result ok from an apply".

### Task 2: `write_only` in catalog examples

**Files:**
- Modify: `tools/generate-docs.yml` (example item `options`: `write_only: {type: dict}`), `tools/templates/example.yml.j2` (render `write_only:` below `fields` when set), `tools/templates/example-field-names.j2` (add the example items' `write_only` keys, flattened like `fields`)

**Interfaces:**
- Produces: a catalog example item may hold `write_only` (dict, same shape as `fields`); the generated example task shows it below `fields`; `make docs` checks its names against the field file like `fields`; integration tests pass `item[0]['items']` unchanged, so `write_only` reaches the module.

`tools/tests/` holds no docs fixtures, so the check runs on a temporary edit of `meta/areas.yml` that is reverted afterwards.

- [ ] **Step 1: Write the failing check:** in `meta/areas.yml`, give the first item of the `dnsmasq_host` example `write_only: {descr: x}`. Run `make docs`. Expected: FAIL on the argument spec, naming `write_only` as unsupported.
- [ ] **Step 2: Implement** the three changes.
- [ ] **Step 3: Run** `make docs` with the temporary edit. Expected: PASS, the generated example shows `write_only:` with `descr: x`. Change it to `write_only: {nosuchfield: x}`. Expected: FAIL naming `nosuchfield`. Revert `meta/areas.yml`; `make docs-check` shows no change in the generated files.
- [ ] **Step 4:** `make check`; commit -> "Let catalog examples carry write-only values".

### Task 3: Live facts

**Files:** none committed; a throwaway `tests/integration/facts-trust-openvpn.yml`, deleted after the step.

- [ ] **Step 1:** After `make integration-reset`, record through `item` and `ansible.builtin.uri`: (a) add a CA (`descr: routerops facts ca`, write-only `action: internal`, `commonname: rt-facts-ca`) and print the `get` keys and the values of `refid`, `action`, `commonname`, `lifetime`; (b) add a server certificate signed by it (`caref`, `cert_type: server_cert`) and print the same; (c) rerun both without changes -> `changed=0`?; (d) GET `openvpn/instances/gen_key/tls-crypt` and print the key's first line and line count; add a static key with it, GET it back and record whether the stored `key` equals the sent one byte for byte (newlines); (e) add an instance (port `11940`, `server: 10.250.80.0/24`, the certificate's refid), POST `openvpn/service/reconfigure` and record the answer, then GET `openvpn/service/search_sessions` and record whether the instance runs; (f) `trust/cert/del` while the instance uses it -> record status and body; (g) `make fields ID=` for the Ca.xml and Cert.xml nodes works (node `ca`, `cert`). Reset the VM; delete the playbook.
- [ ] **Step 2:** If (c) shows a change or (d) a key mismatch, stop and report; the entries below assume `changed=0` and a byte-identical key.

### Task 4: Trust CA and certificate

**Files:**
- Modify: `meta/areas.yml`, generated files (`make docs`), `docs/testing.md`
- Create: `meta/fields/trust_ca.yml`, `meta/fields/trust_cert.yml`, `tests/integration/test-trust-ca-item.yml`, `tests/integration/test-trust-cert-item.yml`

- [ ] **Step 1: Catalog entries** (values from the tables, `stage: v0`, `tested: ["26.7.7"]`). `trust_ca`: `area: trust`, `title: Certificate authority`, `lookup: [descr]`, `write_only: [action, key_type, digest, lifetime, commonname, country, city, state, organization, organizationalunit, email]`, no `apply`; note: "The fields that create the CA (`action`, `commonname`, key and lifetime settings) are not stored, so they go in `write_only` and are sent only when the CA is added. Read the `refid` that certificates and OpenVPN refer to with `return_fields: [refid]`. OPNsense deletes a CA even while certificates or instances use it. The private key is readable through the API. Descriptions identify a CA; keep them unique." Examples: "Create an internal CA" (`fields: {descr: routerops example ca}`, `write_only: {action: internal, commonname: routerops-example-ca, country: AT}`, `return_fields: [refid]`), "Remove a CA" (`descr`, `state: absent`). `trust_cert`: `title: Certificate`, `lookup: [descr]`, `write_only: [action, key_type, digest, lifetime, cert_type, private_key_location, commonname, country, city, state, organization, organizationalunit, email, altnames_dns, altnames_ip, altnames_uri, altnames_email]`; note: "`caref` is the `refid` of the signing CA. Every update reissues the certificate with the same key. A certificate an OpenVPN instance uses cannot be deleted; OPNsense answers HTTP 500 \"Item in use by\". The private key is readable through the API." The note adds: "In the examples, replace `EXAMPLE_CA_REFID` with the `refid` the CA example returns." Examples: "Create a server certificate" (`fields: {descr: routerops example server, caref: EXAMPLE_CA_REFID}`, `write_only: {action: internal, cert_type: server_cert, commonname: rt-example-server}`, `return_fields: [refid]`), "Remove a certificate".
- [ ] **Step 2: Run** `make fields ID=trust_ca`, `make fields ID=trust_cert`, `make docs`. Expected: the volatile fields show "not stored" in `docs/areas/trust.md`.
- [ ] **Step 3: Write the CA test** in the plan 4c.1 Task 3 pattern: CAs `routerops test ca` and `routerops test two` (write-only `action: internal`, `commonname`), check-mode add, add with `return_fields: [refid]` asserting a 13-hex `refid`, rerun `changed=0`, check-mode rerun, update `descr` of the second, delete, invalid `caref: 0000000000000` -> `validations` naming `ca.caref`, examples twice, cleanup with query.
- [ ] **Step 4: Write the certificate test:** a first block task adds the CA `routerops test ca` and registers its `refid`; certificates `routerops test server` and `routerops test two` signed by it (`cert_type: server_cert`) in the plan 4c.1 Task 3 pattern; the rerun also GETs the certificate's `crt` before and after and asserts it is equal (no reissue); update `descr` once; invalid `caref: 0000000000000` -> `validations` naming `cert.caref`; examples twice with `EXAMPLE_CA_REFID` replaced by the refid of the CA example, which the block adds first; `always`: certificates, then CAs; query all and assert gone.
- [ ] **Step 5: Run** `make integration-reset`, `make integration-local TARGET=test-trust-ca-item`, then `TARGET=test-trust-cert-item`. Expected: `failed=0` each.
- [ ] **Step 6: Fault check:** a copy of the certificate test with `update_write_only: always` on the rerun must FAIL the `changed=0` and the `crt` equality asserts. Reset the VM.
- [ ] **Step 7:** `make check`, verified-runs rows, commit -> "Add the Trust CA and certificate areas".

### Task 5: OpenVPN instance

**Files:** as Task 4 for `openvpn_instance`, test `test-openvpn-instance-item.yml`.

- [ ] **Step 1: Catalog entry:** `area: openvpn`, `title: OpenVPN instance`, `key: instance`, `lookup: [description]`, `secret_fields: [password]`, apply `openvpn/service/reconfigure`, both privileges; note: "`cert` and `ca` take a `refid` from the Trust areas; `tls_key` takes the uuid of a static key. OPNsense numbers instances itself (`vpnid`); never send it. The apply starts, restarts or stops every changed instance. Descriptions identify an instance; keep them unique." The note adds: "In the examples, replace `EXAMPLE_CERT_REFID` with the `refid` the certificate example returns." Examples: "Run an OpenVPN server" (`role: server`, `dev_type: tun`, `proto: udp`, `port: "11942"`, `server: 10.250.82.0/24`, `cert: EXAMPLE_CERT_REFID`, `description: routerops example`), "Remove an OpenVPN instance".
- [ ] **Step 2: Run** `make fields ID=openvpn_instance`, `make docs`.
- [ ] **Step 3: Write the test:** a first block task adds the CA and the server certificate (catalog entries, registers the cert refid) and the example's CA and certificate; instances `routerops test one` (`11940`, `10.250.80.0/24`) and `routerops test two` (`11941`, `10.250.81.0/24`) in the plan 4c.1 Task 3 pattern; update `verb: "4"` on one; invalid `cert: 0000000000000` -> `validations` naming `instance.cert`; examples twice with `EXAMPLE_CERT_REFID` replaced; `always`: instances, certificates, CAs, in that order; query all and assert gone.
- [ ] **Step 4-6:** `make integration-reset`, run, fault check (idempotency; a copy whose apply answer check is reverted to `status` only must FAIL on the apply), `make check`, verified-runs row, commit -> "Add the OpenVPN instance area".

### Task 6: OpenVPN static key

**Files:** as Task 4 for `openvpn_static_key`, test `test-openvpn-static-key-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: OpenVPN static key`, `key: statickey`, actions from the table, `lookup: [description]`, `secret_fields: [key]`, apply `openvpn/service/reconfigure`; note: "Generate `key` with `openvpn/instances/gen_key/tls-crypt` (or `tls-auth`, `tls-crypt-v2-server` to match `mode`). OPNsense deletes a key even while an instance uses it as `tls_key`. The key is readable through the API." The note adds: "In the examples, replace `EXAMPLE_STATIC_KEY` with a generated key." Examples: "Add a TLS crypt key" (`mode: crypt`, `key: EXAMPLE_STATIC_KEY`, `description: routerops example`), "Remove a static key".
- [ ] **Step 2: Run** `make fields ID=openvpn_static_key`, `make docs`.
- [ ] **Step 3: Write the test:** `ansible.builtin.uri` GET `openvpn/instances/gen_key/tls-crypt` three times (`no_log: true`), register the keys; keys `routerops test one` and `two` in the plan 4c.1 Task 3 pattern; the add result shows `key` masked in the diff (assert the diff text does not hold the key's second line); update `mode: auth` with a `tls-auth` key; invalid `key: "bad_key!"` -> `validations` naming `statickey.key`; examples twice with `EXAMPLE_STATIC_KEY` replaced by the third key; cleanup with query.
- [ ] **Step 4-6:** run, fault check (idempotency; a copy without `secret_fields` must FAIL the masking assert), `make check`, verified-runs row, commit -> "Add the OpenVPN static key area".

### Task 7: OpenVPN client-specific override

**Files:** as Task 4 for `openvpn_cso`, test `test-openvpn-cso-item.yml`.

- [ ] **Step 1: Catalog entry:** `title: OpenVPN client-specific override`, `key: cso`, `lookup: [common_name]`, no `apply`, privilege `page-openvpn-csc`; note: "OpenVPN reads the overrides when a client connects; there is nothing to apply. An empty `servers` applies the override to every server; otherwise list instance uuids." Examples: "Give a client a fixed tunnel address" (`common_name: rt-example-client`, `tunnel_network: 10.250.82.10/24`, `description: routerops example`), "Remove an override".
- [ ] **Step 2: Run** `make fields ID=openvpn_cso`, `make docs`.
- [ ] **Step 3: Write the test:** overrides `rt-test-client-one` and `rt-test-client-two` in the plan 4c.1 Task 3 pattern; update `block: true`; invalid `tunnel_network: 10.250.80.300/24` -> `validations` naming `cso.tunnel_network`; examples twice; cleanup with query.
- [ ] **Step 4-6:** run, fault check (idempotency), `make check`, verified-runs row, commit -> "Add the OpenVPN client-specific override area".

### Task 8: Scenario CA -> certificate -> OpenVPN instance

**Files:**
- Create: `tests/integration/scenario-ca-cert-openvpn.yml`
- Modify: `docs/testing.md`

- [ ] **Step 1: Write the scenario:** add CA `routerops scenario ca` (`return_fields: [refid]`), add certificate `routerops scenario server` with its refid, add instance `routerops scenario` (`11943`, `10.250.83.0/24`) with the certificate refid; rerun all three `changed=0`; delete the certificate -> `failed`, message holds "in use"; the certificate query still finds it. `always`: instance, certificate, CA in that order; query all three and assert gone.
- [ ] **Step 2: Run** `make integration-local TARGET=scenario-ca-cert-openvpn`. Expected: `failed=0`.
- [ ] **Step 3: Fault check:** a copy that deletes the instance before the certificate must FAIL on the "in use" assert. Reset the VM.
- [ ] **Step 4:** `make check`; verified-runs row; commit -> "Add the CA -> certificate -> OpenVPN scenario".

### Task 9: Close plan 4d.1

**Files:** `docs/superpowers/plans/2026-10-17-v0-tracking.md`, `docs/testing.md`, `changelogs/fragments/areas-vpn.yml`

- [ ] **Step 1:** Fragment `minor_changes`: "Documentation - the area catalog gains Trust (CA, certificate) and OpenVPN (instance, static key, client-specific override), each tested against OPNsense 26.7.7."; plans 4d.2 and 4d.3 extend the same fragment.
- [ ] **Step 2:** Tracking row 5, facts for `docs/limits.md`: a CA can be deleted while certificates or instances use it; every certificate update reissues it; Trust private keys, static keys and the instance `password` are readable through the API; OpenVPN apply needs `page-status-openvpn`.
- [ ] **Step 3:** `make integration-reset`, `make integration-local` (everything). Expected: every play `failed=0`. Verified-runs row.
- [ ] **Step 4:** tracking row 4d.1 -> done; `make check`; commit -> "Close plan 4d.1".
