# Testing

`make check` runs lint, sanity and unit tests without any OPNsense. Integration tests run by hand against a dedicated OPNsense VM, never against a production router.

## Test VM

| Item | Setting |
|---|---|
| Host | the owner's Proxmox |
| WAN, LAN | two bridges without a physical port (`vmbr` without `bridge-ports`), so the VM can neither hand out DHCP nor answer as a gateway on a real network |
| Test host | sits on the LAN bridge and reaches the web interface there |
| Plugins | `os-acme-client`, `os-node_exporter`, `os-mdns-repeater` installed before the snapshot |
| Snapshot | `clean`, taken after installation, plugins and the API user |
| TLS | the VM's self-signed certificate; `OPNSENSE_VALIDATE_CERTS=false` is only for this VM |

## Run

| Step | Command |
|---|---|
| Reset the VM | `qm rollback <vmid> clean` on the Proxmox host (by hand; `make integration` has no Proxmox access) |
| All tests | `OPNSENSE_INTEGRATION=1 OPNSENSE_URL=https://<vm> OPNSENSE_API_KEY=... OPNSENSE_API_SECRET=... OPNSENSE_VALIDATE_CERTS=false make integration` |
| One test | the same with `TARGET=settings_nodeexporter` |

## API privileges

The API user gets only the privileges the tests need, read from each area's `ACL.xml`.

| Test | Privilege | Source |
|---|---|---|
| `settings_nodeexporter` | `page-services-nodeexporter` ("Services: Prometheus Exporter", `api/nodeexporter/*`) | `opnsense-plugins/sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/ACL/ACL.xml` |
