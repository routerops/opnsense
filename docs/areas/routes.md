<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `routes`

## Static route

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `routes/routes` |
| Key | `route` |
| Actions | `add: addroute`, `del: delroute`, `get: getroute`, `search: searchroute`, `set: setroute` |
| Lookup | `network` |
| Apply | `routes/routes/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-system-staticroutes` ("System: Static Routes", `api/routes/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

The gateway a route names must exist before the route; OPNsense caches its gateway list for 20 seconds, so a route sent right after a new gateway can fail validation.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Routes/Route.xml#route`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `network` | NetworkField | yes |  |  |
| `gateway` | JsonKeyValueStoreField | yes |  |  |
| `descr` | DescriptionField |  |  |  |
| `enabled` | BooleanField | yes | `1` |  |

### Examples

```yaml
- name: Route a remote network through a LAN gateway
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routes/routes"
    key: "route"
    lookup: ["network"]
    actions:
      add: "addroute"
      del: "delroute"
      get: "getroute"
      search: "searchroute"
      set: "setroute"
    apply: "routes/routes/reconfigure"
    items:
      - fields:
          network: "10.99.0.0/24"
          gateway: "RT_EXAMPLE_GW"
          descr: "routerops example"

- name: Keep only the listed static routes
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routes/routes"
    key: "route"
    lookup: ["network"]
    actions:
      add: "addroute"
      del: "delroute"
      get: "getroute"
      search: "searchroute"
      set: "setroute"
    apply: "routes/routes/reconfigure"
    purge: true
    items:
      - fields:
          network: "10.99.0.0/24"
          gateway: "RT_EXAMPLE_GW"
          descr: "routerops example"
      - fields:
          network: "10.99.1.0/24"
          gateway: "RT_EXAMPLE_GW"
          descr: "routerops example"

- name: Remove a static route
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routes/routes"
    key: "route"
    lookup: ["network"]
    actions:
      add: "addroute"
      del: "delroute"
      get: "getroute"
      search: "searchroute"
      set: "setroute"
    apply: "routes/routes/reconfigure"
    items:
      - fields:
          network: "10.99.1.0/24"
        state: "absent"
```
