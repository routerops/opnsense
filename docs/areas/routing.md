<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `routing`

## Gateway

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `routing/settings` |
| Key | `gateway_item` |
| Actions | `add: addGateway`, `del: delGateway`, `get: getGateway`, `search: searchGateway`, `set: setGateway` |
| Lookup | `name` |
| Item ids | `uuid` |
| Apply | `routing/settings/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-system-gateways` ("System: Gateways", `api/routing/settings/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Gateways OPNsense generates for dynamic interfaces, such as `WAN_DHCP`, carry their name as `uuid` and are not items of this area: `present` and `absent` do not find them, so `present` with such a name sends an add; `state: query` finds them.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Routing/Gateways.xml#gateway_item`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `disabled` | BooleanField | yes | `0` |  |
| `name` | TextField | yes |  |  |
| `descr` | DescriptionField |  |  |  |
| `interface` | InterfaceField | yes | `wan` |  |
| `ipprotocol` | OptionField | yes | `inet` | `inet`, `inet6` |
| `gateway` | TextField |  |  |  |
| `defaultgw` | BooleanField |  |  |  |
| `fargw` | BooleanField |  |  |  |
| `monitor_disable` | BooleanField | yes | `1` |  |
| `monitor_noroute` | BooleanField |  |  |  |
| `monitor_killstates` | BooleanField |  |  |  |
| `monitor_killstates_priority` | BooleanField |  |  |  |
| `monitor` | TextField |  |  |  |
| `force_down` | BooleanField |  |  |  |
| `nosync` | BooleanField |  |  |  |
| `priority` | IntegerField | yes | `255` |  |
| `weight` | IntegerField | yes | `1` |  |
| `latencylow` | IntegerField |  |  |  |
| `latencyhigh` | IntegerField |  |  |  |
| `losslow` | IntegerField |  |  |  |
| `losshigh` | IntegerField |  |  |  |
| `interval` | IntegerField |  |  |  |
| `time_period` | IntegerField |  |  |  |
| `loss_interval` | IntegerField |  |  |  |
| `data_length` | IntegerField |  |  |  |

### Examples

```yaml
- name: Add a LAN gateway
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routing/settings"
    key: "gateway_item"
    lookup: ["name"]
    actions:
      add: "addGateway"
      del: "delGateway"
      get: "getGateway"
      search: "searchGateway"
      set: "setGateway"
    apply: "routing/settings/reconfigure"
    items:
      - fields:
          name: "RT_EXAMPLE_GW"
          interface: "lan"
          gateway: "10.250.1.254"
          descr: "routerops example"

- name: Remove a gateway
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routing/settings"
    key: "gateway_item"
    lookup: ["name"]
    actions:
      add: "addGateway"
      del: "delGateway"
      get: "getGateway"
      search: "searchGateway"
      set: "setGateway"
    apply: "routing/settings/reconfigure"
    items:
      - fields:
          name: "RT_EXAMPLE_GW"
        state: "absent"
```
