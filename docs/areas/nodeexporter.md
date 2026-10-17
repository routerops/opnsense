<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `nodeexporter`

## node_exporter general

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.settings` |
| Path | `nodeexporter/general` |
| Key | `general` |
| Actions | default |
| Lookup | - |
| Apply | `nodeexporter/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-nodeexporter` ("Services: Prometheus Exporter", `api/nodeexporter/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | `os-node_exporter` |
| Stage | v0 |

### Fields

Read from `opnsense/plugins@26.7.7:sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/General.xml`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `0` |  |
| `listenaddress` | NetworkField | yes | `0.0.0.0` |  |
| `listenport` | PortField | yes | `9100` |  |
| `cpu` | BooleanField |  |  |  |
| `exec` | BooleanField |  |  |  |
| `filesystem` | BooleanField |  |  |  |
| `loadavg` | BooleanField |  |  |  |
| `meminfo` | BooleanField |  |  |  |
| `netdev` | BooleanField |  |  |  |
| `time` | BooleanField |  |  |  |
| `devstat` | BooleanField |  |  |  |
| `interrupts` | BooleanField |  |  |  |
| `ntp` | BooleanField |  |  |  |
| `zfs` | BooleanField |  |  |  |

### Example

```yaml
- name: Enable node_exporter on port 9100
  routerops.opnsense.settings:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "nodeexporter/general"
    key: "general"
    apply: "nodeexporter/service/reconfigure"
    fields:
      enabled: true
      listenport: 9100
```
