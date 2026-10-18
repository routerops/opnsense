# Testing

`make check` runs lint, sanity and unit tests without any OPNsense. Integration tests run by hand against a dedicated OPNsense VM, never against a production router.

## Test VM

| Item | Setting |
|---|---|
| Host | the owner's Proxmox |
| OPNsense | latest 26.7.x, at least 26.7.6 (the interface assignment tests need it); currently 26.7.7 (amd64, FreeBSD 15.1-RELEASE-p4) |
| VM | VMID 9090 (`opnsense-test`), `onboot 0`, disk excluded from backups (`backup=0`) |
| WAN | `vtnet0` on `vmbr-optwan`, a bridge without a physical port: VM 10.250.0.2/30, the Proxmox host 10.250.0.1 as gateway, DNS 1.1.1.1; the host masquerades it, and the nft table `opnsense_test` lets the VM reach the internet but neither the home network nor the ISP network |
| LAN | `vtnet1` on `vmbr-optlan`, a bridge without a physical port: VM 10.250.1.1/24, the Proxmox host 10.250.1.2; DHCP is off (dhcpd and Kea not running, port 67 closed) |
| Access | the Proxmox host forbids SSH port forwarding, so `socat` forwards a local port through `ssh root@<proxmox-host> nc 10.250.1.1 443`: `socat TCP-LISTEN:8443,bind=127.0.0.1,reuseaddr,fork EXEC:"ssh -o BatchMode=yes root@<proxmox-host> nc 10.250.1.1 443"` |
| Plugins | `os-acme-client` 4.17, `os-node_exporter` 1.2, `os-mdns-repeater` 1.2, installed before the snapshot |
| API user | `ansible-test`, no shell, only the privileges in the table below |
| Snapshot | `clean`, taken with the VM shut down and the ISO ejected, after the update, the plugins and the API user |
| TLS | the VM's self-signed certificate; `OPNSENSE_VALIDATE_CERTS=false` is only for this VM |

## Run

Run from the repository root while the tunnel is open. The secret is read without echo and never lands in the shell history.

```sh
read -r "OPNSENSE_API_KEY?API key: "; read -rs "OPNSENSE_API_SECRET?API secret: "; echo
export OPNSENSE_API_KEY OPNSENSE_API_SECRET OPNSENSE_URL=https://127.0.0.1:8443 OPNSENSE_VALIDATE_CERTS=false
OPNSENSE_INTEGRATION=1 make integration TARGET=test-nodeexporter-general-settings
unset OPNSENSE_API_KEY OPNSENSE_API_SECRET OPNSENSE_URL OPNSENSE_VALIDATE_CERTS
```

Omit `TARGET` to run every test. Scenario playbooks (`scenario-*.yml`) run after the area tests; `TARGET=scenario-<name>` runs one alone. Reset the VM between runs on the Proxmox node: `qm rollback 9090 clean && qm start 9090` (VMID 9090 on the owner's node); `make integration` has no Proxmox access.

A test whose catalog entry names a `plugin` fails when the endpoint is not found. On a target without that plugin, set `OPNSENSE_SKIP_MISSING_PLUGINS=1` to end the play with a skip message instead; the test VM has every plugin installed, so runs against it leave the variable unset.

A new check counts only after it failed once against a real fault: copy the test playbook outside the repository, change one wanted value in the idempotency task, run it with `ANSIBLE_COLLECTIONS_PATH=$PWD/build .venv/bin/ansible-playbook <copy>` and see the assert fail, then roll the VM back.

## Unattended local run

`make integration-local` opens the tunnel itself, reads the credentials, runs `make integration` and closes the tunnel again; an agent can run it without help.

| Input | Source |
|---|---|
| `PROXMOX_HOST` | set in the untracked `integration.local.mk` (gitignored), which the Makefile includes |
| Tunnel | `socat` on `127.0.0.1:18443` (`TUNNEL_PORT`) forwarding through `ssh -o BatchMode=yes root@$PROXMOX_HOST nc 10.250.1.1 443` |
| API key and secret | the Bitwarden login item `routerops-opnsense-test` (username = key, password = secret), read with `bw get` in a silent recipe line; `bw` must be unlocked |

Nothing is printed or written to a file; the values exist only in the environment of the test run.

## API privileges

The API user gets only the privileges the tests need, read from each area's `ACL.xml`.

<!-- BEGIN privileges: generated from meta/areas.yml by make docs -->
| Test | Privilege | Source |
|---|---|---|
| `test-dnsmasq-domain-override-item` | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` |
| `test-dnsmasq-general-settings` | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` |
| `test-dnsmasq-host-item` | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` |
| `test-dnsmasq-option-item` | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` |
| `test-dnsmasq-range-item` | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` |
| `test-firewall-alias-item` | `page-firewall-alias-edit` ("Firewall: Alias: Edit", `api/firewall/alias/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml` |
| `test-firewall-destination-nat-item` | `page-firewall-nat-portforward-edit` ("Firewall: NAT: Destination NAT", `api/firewall/d_nat/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml` |
| `test-firewall-filter-rule-item` | `page-filter-api` ("Firewall: Rules [new]", `api/firewall/filter/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Firewall/ACL/ACL.xml` |
| `test-firewall-one-to-one-nat-item` | `page-firewall-nat-1-1-edit` ("Firewall: NAT: 1:1", `api/firewall/one_to_one/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Firewall/ACL/ACL.xml` |
| `test-firewall-source-nat-item` | `page-filter-snat-api` ("Firewall: NAT: Source NAT", `api/firewall/source_nat/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Firewall/ACL/ACL.xml` |
| `test-firewall-source-nat-general-settings` | `page-filter-snat-api` ("Firewall: NAT: Source NAT", `api/firewall/source_nat/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Firewall/ACL/ACL.xml` |
| `test-interfaces-assignment-item` | `page-interfaces-assignnetworkports` ("Interfaces: Assign network ports", `api/interfaces/assignment/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml` |
| `test-interfaces-vip-item` | `page-firewall-virtualipaddress-edit` ("Interfaces: Virtual IPs: Settings", `api/interfaces/vip_settings/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Interfaces/ACL/ACL.xml` |
| `test-interfaces-vlan-item` | `page-interfaces-vlan-edit` ("Interfaces: VLAN", `api/interfaces/vlan_settings/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Interfaces/ACL/ACL.xml` |
| `test-kea-dhcpv4-general-settings` | `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", `api/kea/dhcpv4/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Kea/ACL/ACL.xml` |
| `test-kea-dhcpv4-reservation-item` | `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", `api/kea/dhcpv4/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Kea/ACL/ACL.xml` |
| `test-kea-dhcpv4-subnet-item` | `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", `api/kea/dhcpv4/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Kea/ACL/ACL.xml` |
| `test-nodeexporter-general-settings` | `page-services-nodeexporter` ("Services: Prometheus Exporter", `api/nodeexporter/*`) | `opnsense-plugins/sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/ACL/ACL.xml` |
| `test-routes-static-route-item` | `page-system-staticroutes` ("System: Static Routes", `api/routes/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml` |
| `test-routing-gateway-item` | `page-system-gateways` ("System: Gateways", `api/routing/settings/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml` |
| `test-unbound-acl-item` | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Unbound/ACL/ACL.xml` |
| `test-unbound-forward-item` | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Unbound/ACL/ACL.xml` |
| `test-unbound-general-settings` | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Unbound/ACL/ACL.xml` |
| `test-unbound-host-alias-item` | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Unbound/ACL/ACL.xml` |
| `test-unbound-host-override-item` | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Unbound/ACL/ACL.xml` |
<!-- END privileges: generated from meta/areas.yml by make docs -->

## Verified runs

| Date | OPNsense | Test | Result |
|---|---|---|---|
| 17.10.2026 | 26.7.7 | `test-nodeexporter-general-settings` | passed (`failed=0`, one ignored expected failure); the fault-injected copy failed on the idempotency assert as intended |
| 17.10.2026 | 26.7.7 | `test-dnsmasq-host-item` | passed (`failed=0`, one ignored expected failure); the fault-injected copy failed on the idempotency assert as intended |
| 17.10.2026 | 26.7.7 | `test-firewall-alias-item` | passed (`failed=0`); the fault-injected copy failed on the idempotency assert as intended |
| 17.10.2026 | 26.7.7 | `test-dnsmasq-host-item` | passed with the area read from `meta/areas.yml` and the catalog example run twice (`failed=0`, one ignored expected failure) |
| 17.10.2026 | 26.7.7 | `test-firewall-alias-item` | passed with the area read from `meta/areas.yml` and the catalog example run twice (`failed=0`); the fault-injected copy failed on the example idempotency assert as intended |
| 17.10.2026 | 26.7.7 | `test-nodeexporter-general-settings` | passed with the area read from `meta/areas.yml` and the catalog example run twice (`failed=0`, one ignored expected failure); a copy with a wrong path ended the play with the missing-plugin message, `failed=0` |
| 17.10.2026 | 26.7.7 | `test-dnsmasq-host-item` | passed with connection options from the environment and the example list (add, purge, delete), each example run twice (`failed=0`, one ignored expected failure) |
| 17.10.2026 | 26.7.7 | `test-firewall-alias-item` | passed with `secret_fields` on a `urltable` alias password (a copy without it failed on the leak assert), `state: query` on `bogons` (type `external`; a copy expecting another type failed) and `return_fields` (`failed=0`) |
| 17.10.2026 | 26.7.7 | `test-nodeexporter-general-settings` | passed with connection options from the environment (`failed=0`, one ignored expected failure) |
| 18.10.2026 | 26.7.7 | `test-firewall-filter-rule-item` | passed (`failed=0`, one ignored expected failure); the fresh VM lists 17 automatic rules with md5 ids, and a build from `main` without the non-MVC row fix failed on the purge assert; the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-firewall-destination-nat-item` | passed with a nested `destination.port` update and an unchanged rerun (`failed=0`, one ignored expected failure); the fault-injected copy failed on the nested idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-firewall-source-nat-general-settings` | passed with the original mode restored in `always` (`failed=0`, one ignored expected failure); OPNsense rejects an unknown mode with "Option [] not in list." |
| 18.10.2026 | 26.7.7 | `test-firewall-source-nat-item` | passed in `hybrid` mode with the original mode restored after the cleanup (`failed=0`, one ignored expected failure); the copy without the mode switch failed on the rerun assert (duplicate add) as intended |
| 18.10.2026 | 26.7.7 | `test-firewall-one-to-one-nat-item` | passed with the `purge` example run twice (`failed=0`, one ignored expected failure: "External subnet should match internal subnet."); the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-routing-gateway-item` | passed (`failed=0`, one ignored expected failure); the check-mode `purge` listed one gateway the VM already holds, a UUID row, and no generated gateway; the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-routes-static-route-item` | passed with the `purge` example run twice (`failed=0`, one ignored expected failure); the fault-injected copy failed on the idempotency assert as intended; after a route write that fills the gateway cache before the gateway exists, a copy without the 21 s pause failed on `route.gateway` and the copy with it passed |
| 18.10.2026 | 26.7.7 | `scenario-alias-filter-rule` | passed (`failed=0`, one ignored expected failure); deleting the alias a filter rule uses answers HTTP 500 "Alias in use: Cannot delete alias rt_scenario_hosts. Currently in use by [OPNsense.Firewall.Filter.rules.rule.2/destination_net]", naming the alias and the rule's model path, not its description; a copy whose rule does not use the alias failed on the `failed` assert as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and `scenario-alias-filter-rule` in one `make integration-local` | the first full run failed in `test-firewall-alias-item`: the non-MVC row filter hid the built-in alias `bogons`, whose search `uuid` is its name, from `state: query`; after the fix all eleven plays passed (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-firewall-source-nat-item`, `test-routes-static-route-item`, `test-firewall-alias-item` | passed after the review fixes (`query` prefers UUID rows, mode restore before the last assert, gateway lookup after the route cleanup) (`failed=0`); a route test copy that skips the gateway removal failed on the new gateway assert as intended |
| 17.10.2026 | 26.7.7 | `test-dnsmasq-host-item`, `test-firewall-alias-item` | passed with a cleanup check that queries every catalog example after the `always` block; the earlier runs above left the examples without `state` on the VM, which the new check caught (`failed=1`) before the cleanup filter was fixed |
| 18.10.2026 | 26.7.7 | `test-interfaces-vlan-item` | passed (`failed=0`, one ignored expected failure: tag 4095 answers "Invalid integer value." on `vlan.tag`); the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-interfaces-vip-item` | passed with an update of `network` and an unchanged rerun (`failed=0`, one ignored expected failure: the broadcast address answers "You cannot use the broadcast address." on `vip.network`); the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-interfaces-assignment-item` | passed with `opt` names as outcome ids and an unchanged rerun (`failed=0`, one ignored expected failure: `staticv4` without an address answers "An address is required when configuring static mode" on `interface.ipaddr`); the fault-injected copy failed on the idempotency assert, and a copy run against a build from `main` without `id_format` failed on the rerun with "Device descriptions must be unique." and "Can not assign a device to more interfaces.", as intended |
| 18.10.2026 | 26.7.7 | `scenario-vlan-assignment-vip` | passed with a virtual IP on the assigned VLAN and all three reruns unchanged (`failed=0`, one ignored expected failure: deleting the assigned VLAN answers HTTP 500 "This VLAN cannot be deleted because it is assigned as an interface."); a copy that removes the assignment before the VLAN delete failed on the `failed` assert as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and both scenarios in one `make integration-local` after `make integration-reset` | all fifteen plays passed (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-unbound-general-settings` | passed with the original `txtsupport` restored and checked in `always` (`failed=0`, one ignored expected failure: port 70000 answers "Please specify a valid port number (1-65535)." on `unbound.general.port`); the fault-injected copy failed on the idempotency assert and still restored the setting, as intended |
| 18.10.2026 | 26.7.7 | `test-unbound-host-override-item` | passed (`failed=0`, one ignored expected failure: `rt-test-one.` answers "A valid hostname must be specified." on `host.hostname`); the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-unbound-host-alias-item` | passed with the host override uuid from a registered outcome and the example placeholder `EXAMPLE_HOST_UUID` replaced at run time (`failed=0`, one ignored expected failure: an unknown host uuid answers "Option [] not in list." on `alias.host`); the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-unbound-forward-item` | passed with a port update and an unchanged rerun (`failed=0`, one ignored expected failure: `not-an-address` answers "Please specify a valid network segment or IP address." on `dot.server`); the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-unbound-acl-item` | passed with a rerun whose `networks` are reversed staying unchanged (`failed=0`, one ignored expected failure: `10.250.70.300/24` answers "Please specify a one or more valid network segment in CIDR notation (Ipv4/IPv6)." on `acl.networks`); the fault-injected copy failed on the idempotency assert, and a copy with `ordered_fields: [networks]` on the reversed rerun failed on its assert, as intended |
| 18.10.2026 | 26.7.7 | `scenario-host-override-alias` | passed (`failed=0`): deleting the host override also deleted its alias, so a query for the alias found nothing; a copy that updates the host instead of deleting it failed on the alias-gone assert as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and all three scenarios in one `make integration-local` after `make integration-reset` | all twenty-one plays passed (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-unbound-host-override-item`, `test-unbound-host-alias-item` | passed with the wider lookups (`[hostname, domain, rr]` and `[host, hostname, domain]`): an A and an AAAA record for one name and two aliases that only set a domain are two items each (`failed=0`); with the old lookups both tests failed with "duplicate lookup value" as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and all three scenarios in one `make integration-local` after `make integration-reset` | all twenty-one plays passed after the lookup fix (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-kea-dhcpv4-general-settings` | passed with the original `valid_lifetime` restored and checked in `always` (`failed=0`, one ignored expected failure: `-1` answers "Invalid integer value." on `dhcpv4.general.valid_lifetime`); the apply answers `ok` with Kea disabled; the fault-injected copy failed on the idempotency assert and still restored the value, as intended |
| 18.10.2026 | 26.7.7 | `test-kea-dhcpv4-subnet-item` | passed with a general save between the add and the rerun: OPNsense filled `option_data.routers` of the LAN subnet `10.250.1.0/24`, and the rerun stayed unchanged because no entry sends `option_data` (`failed=0`, one ignored expected failure: `10.250.60.0/33` answers "Please specify a valid network segment or IP address." on `subnet4.subnet`); the fault-injected copy failed on the idempotency assert, and a copy with the second subnet off every interface (`10.250.61.0/24`) failed on the collected-router assert, as intended |
| 18.10.2026 | 26.7.7 | `test-kea-dhcpv4-reservation-item` | passed with one MAC address in two subnets as two items (`failed=0`, one ignored expected failure: an address outside the subnet answers "Address not in specified subnet" on `reservation.ip_address`); the fault-injected copy failed on the idempotency assert as intended. The upper-case rerun in this run sent a MAC address without hex letters and so tested nothing; see the row after the review fixes |
| 18.10.2026 | 26.7.7 | `scenario-subnet-reservation` | passed (`failed=0`, one ignored expected failure): deleting the subnet a reservation uses answers HTTP 500 "Item subnets.subnet4 {routerops test scenario} in use by:" naming the reservation by description and model path; a copy that removes the reservation before the subnet delete failed on the `failed` assert as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and all four scenarios in one `make integration-local` after `make integration-reset` | all twenty-five plays passed (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-kea-dhcpv4-reservation-item`, `scenario-subnet-reservation` | passed with the lookup `[subnet, hw_address, client_id]`: two client id reservations in one subnet are two items, and a rerun with a MAC address in upper case (`02:00:00:00:60:0A` against the stored `...:0a`) fails with "Duplicate entry exists." on `reservation.hw_address` and changes nothing (`failed=0`, two ignored expected failures); with the old lookup the client id pair failed with "duplicate lookup value", and a copy whose rerun keeps the case failed on the `failed` assert, as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and all four scenarios in one `make integration-local` after `make integration-reset` | all twenty-five plays passed after the review fixes (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-dnsmasq-general-settings` | passed with the nested `dhcp.lease_max` raised and the original restored and checked in `always` (`failed=0`, one ignored expected failure: `port: 53` answers "Unbound is currently using this port." on `dnsmasq.port`); Dnsmasq runs on the VM on port 53053, the OPNsense default; the fault-injected copy failed on the idempotency assert and still restored the value, as intended |
| 18.10.2026 | 26.7.7 | `test-dnsmasq-domain-override-item` | passed with two overrides for one domain as two items through the lookup `[domain, ip]` (`failed=0`, one ignored expected failure: `bad domain` answers "Labels must be 1–63 characters, …" on `domainoverride.domain`); the fault-injected copy failed on the idempotency assert, and a copy with the lookup `[domain]` failed with "duplicate lookup value", as intended |
| 18.10.2026 | 26.7.7 | `test-dnsmasq-range-item` | passed with two ranges on `lan` and a lease time update (`failed=0`, one ignored expected failure: an empty `end_addr` answers "End address may only be left empty for static ipv4 ranges." on `range.end_addr`); Dnsmasq served DHCP on the isolated LAN bridge until the cleanup; the fault-injected copy failed on the idempotency assert as intended |
| 18.10.2026 | 26.7.7 | `test-dnsmasq-option-item` | passed with `always_send: [type]`, a value update and a `set_tag` on a `type: set` option that shows a change on both runs, because OPNsense clears it (`failed=0`, one ignored expected failure: no option number answers "Either 'Option' or 'Option6' is required." on `option.option`); an update without `type` answers `saved` on 26.7.7, not HTTP 500 as the code suggested; the fault-injected copy failed on the idempotency assert, and a copy without the `set_tag` failed on its assert, as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and all four scenarios in one `make integration-local` after `make integration-reset` | all twenty-nine plays passed (`failed=0`) |
| 18.10.2026 | 26.7.7 | `test-dnsmasq-domain-override-item` | passed with the lookup `[domain, ip, ipset]`: one domain fed into two external aliases with `ip` empty is two items (`failed=0`, one ignored expected failure); with the lookup `[domain, ip]` the pair failed with "duplicate lookup value" as intended |
| 18.10.2026 | 26.7.7 | all `test-*` and all four scenarios in one `make integration-local` after `make integration-reset` | all twenty-nine plays passed after the review fixes (`failed=0`) |
