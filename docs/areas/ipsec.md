<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `ipsec`

## IPsec connection

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `ipsec/connections` |
| Key | `connection` |
| Actions | `add: addConnection`, `del: delConnection`, `get: getConnection`, `search: searchConnection`, `set: setConnection` |
| Lookup | `description` |
| Item ids | `uuid` |
| Apply | `ipsec/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-vpn-ipsec-connections` ("VPN: IPsec: Connections", `api/ipsec/connections/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Deleting a connection also deletes its local and remote authentications and children. Do not send `local_ts` and `remote_ts`; OPNsense fills them from the children. Enable IPsec first with `ipsec/connections/toggle/1`; while IPsec is disabled, every apply fails with `Service "ipsec" failed to stop.` Every apply reloads the firewall rules. Descriptions identify a connection; keep them unique.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/IPsec/Swanctl.xml#Connections.Connection`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `proposals` | IPsecProposalField, multiple | yes | `default` |  |
| `unique` | OptionField | yes | `no` | `no`, `never`, `keep`, `replace` |
| `aggressive` | BooleanField | yes | `0` |  |
| `version` | OptionField | yes | `0` | `0`, `1`, `2` |
| `mobike` | BooleanField | yes | `1` |  |
| `local_addrs` | IKEAddressField |  |  |  |
| `local_port` | OptionField |  |  | ``, `4500` |
| `remote_addrs` | IKEAddressField |  |  |  |
| `remote_port` | OptionField |  |  | ``, `4500` |
| `encap` | BooleanField | yes | `0` |  |
| `reauth_time` | IntegerField |  |  |  |
| `rekey_time` | IntegerField |  |  |  |
| `over_time` | IntegerField |  |  |  |
| `dpd_delay` | IntegerField |  |  |  |
| `dpd_timeout` | IntegerField |  |  |  |
| `pools` | PoolsField, multiple |  |  |  |
| `send_certreq` | BooleanField | yes | `1` |  |
| `send_cert` | OptionField |  |  | `ifasked`, `never`, `always` |
| `keyingtries` | IntegerField |  |  |  |
| `description` | DescriptionField | yes |  |  |
| `local_ts` | TextField, not stored |  |  |  |
| `remote_ts` | TextField, not stored |  |  |  |

### Examples

```yaml
- name: Add a site-to-site connection
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "connection"
    lookup: ["description"]
    actions:
      add: "addConnection"
      del: "delConnection"
      get: "getConnection"
      search: "searchConnection"
      set: "setConnection"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          description: "routerops example"
          version: "2"
          local_addrs: ["10.250.1.1"]
          remote_addrs: ["10.250.110.4"]

- name: Remove a connection
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "connection"
    lookup: ["description"]
    actions:
      add: "addConnection"
      del: "delConnection"
      get: "getConnection"
      search: "searchConnection"
      set: "setConnection"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          description: "routerops example"
        state: "absent"
```
