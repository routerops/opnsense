# Testing

`make check` runs lint, sanity and unit tests without any OPNsense. Integration tests run by hand against a dedicated OPNsense VM, never against a production router.

## Test VM

| Item | Setting |
|---|---|
| Host | the owner's Proxmox |
| OPNsense | latest 26.7.x, at least 26.7.6 (the interface assignment tests need it) |
| WAN | a bridge without a physical port; the Proxmox host holds the gateway address on it and masquerades it, so the VM can download firmware and plugins but no other machine sees its traffic |
| LAN | a second bridge without a physical port; the Proxmox host holds one address on it; the VM's DHCP server is off |
| Access | an SSH tunnel through the Proxmox host to the VM's LAN address, for example `ssh -L 8443:<vm-lan-ip>:443 <proxmox-host>` |
| Plugins | `os-acme-client`, `os-node_exporter`, `os-mdns-repeater` installed before the snapshot |
| API user | `ansible-test`, only the privileges in the table below |
| Snapshot | `clean`, taken after the update, the plugins and the API user |
| TLS | the VM's self-signed certificate; `OPNSENSE_VALIDATE_CERTS=false` is only for this VM |

## Run

Run from the repository root while the tunnel is open. The secret is read without echo and never lands in the shell history.

```sh
read -r "OPNSENSE_API_KEY?API key: "; read -rs "OPNSENSE_API_SECRET?API secret: "; echo
export OPNSENSE_API_KEY OPNSENSE_API_SECRET OPNSENSE_URL=https://127.0.0.1:8443 OPNSENSE_VALIDATE_CERTS=false
OPNSENSE_INTEGRATION=1 make integration TARGET=settings_nodeexporter
unset OPNSENSE_API_KEY OPNSENSE_API_SECRET OPNSENSE_URL OPNSENSE_VALIDATE_CERTS
```

Omit `TARGET` to run every test. Reset the VM between runs on the Proxmox node: `qm rollback <vmid> clean && qm start <vmid>`; `make integration` has no Proxmox access.

A new check counts only after it failed once against a real fault: copy the test playbook outside the repository, change one wanted value in the idempotency task, run it with `ANSIBLE_COLLECTIONS_PATH=$PWD/build .venv/bin/ansible-playbook <copy>` and see the assert fail, then roll the VM back.

## API privileges

The API user gets only the privileges the tests need, read from each area's `ACL.xml`.

| Test | Privilege | Source |
|---|---|---|
| `settings_nodeexporter` | `page-services-nodeexporter` ("Services: Prometheus Exporter", `api/nodeexporter/*`) | `opnsense-plugins/sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/ACL/ACL.xml` |

## Verified runs

| Date | OPNsense | Test | Result |
|---|---|---|---|
| 17.10.2026 | 26.7.x (at least 26.7.6) | `settings_nodeexporter` | passed (`failed=0`, one ignored expected failure); the fault-injected copy failed on the idempotency assert as intended |
