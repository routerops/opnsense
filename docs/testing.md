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
| Access | an SSH tunnel through the Proxmox host: `ssh -L 8443:10.250.1.1:443 <proxmox-host>` |
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

Omit `TARGET` to run every test. Reset the VM between runs on the Proxmox node: `qm rollback 9090 clean && qm start 9090` (VMID 9090 on the owner's node); `make integration` has no Proxmox access.

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
| `test-dnsmasq-host-item` | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` |
| `test-firewall-alias-item` | `page-firewall-alias-edit` ("Firewall: Alias: Edit", `api/firewall/alias/*`) | `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml` |
| `test-nodeexporter-general-settings` | `page-services-nodeexporter` ("Services: Prometheus Exporter", `api/nodeexporter/*`) | `opnsense-plugins/sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/ACL/ACL.xml` |
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
| 17.10.2026 | 26.7.7 | `test-dnsmasq-host-item`, `test-firewall-alias-item` | passed with a cleanup check that queries every catalog example after the `always` block; the earlier runs above left the examples without `state` on the VM, which the new check caught (`failed=1`) before the cleanup filter was fixed |
