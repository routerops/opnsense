<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `dnsmasq`

## Dnsmasq host

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `dnsmasq/settings` |
| Key | `host` |
| Actions | `add: addHost`, `del: delHost`, `get: getHost`, `search: searchHost`, `set: setHost` |
| Lookup | `host`, `domain` |
| Item ids | `uuid` |
| Apply | `dnsmasq/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Dnsmasq/Dnsmasq.xml#hosts`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `host` | HostnameField |  |  |  |
| `domain` | HostnameField |  |  |  |
| `local` | BooleanField |  |  |  |
| `ip` | NetworkField |  |  |  |
| `cnames` | HostnameField |  |  |  |
| `client_id` | TextField |  |  |  |
| `hwaddr` | MacAddressField |  |  |  |
| `lease_time` | IntegerField |  |  |  |
| `ignore` | BooleanField |  |  |  |
| `set_tag` | ModelRelationField |  |  |  |
| `descr` | TextField |  |  |  |
| `comments` | TextField |  |  |  |
| `aliases` | HostnameField |  |  |  |

### Examples

```yaml
- name: Add a Dnsmasq host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "host"
    lookup: ["host", "domain"]
    actions:
      add: "addHost"
      del: "delHost"
      get: "getHost"
      search: "searchHost"
      set: "setHost"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          host: "printer"
          domain: "example.test"
          ip: "192.0.2.10"

- name: Keep only the listed Dnsmasq hosts
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "host"
    lookup: ["host", "domain"]
    actions:
      add: "addHost"
      del: "delHost"
      get: "getHost"
      search: "searchHost"
      set: "setHost"
    apply: "dnsmasq/service/reconfigure"
    purge: true
    items:
      - fields:
          host: "printer"
          domain: "example.test"
          ip: "192.0.2.10"
      - fields:
          host: "scanner"
          domain: "example.test"
          ip: "192.0.2.11"

- name: Remove a Dnsmasq host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "host"
    lookup: ["host", "domain"]
    actions:
      add: "addHost"
      del: "delHost"
      get: "getHost"
      search: "searchHost"
      set: "setHost"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          host: "scanner"
          domain: "example.test"
        state: "absent"
```
