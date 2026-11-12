<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `ipsec`

## IPsec child

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `ipsec/connections` |
| Key | `child` |
| Actions | `add: addChild`, `del: delChild`, `get: getChild`, `search: searchChild`, `set: setChild` |
| Lookup | `connection`, `description` |
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

`connection` is the uuid of an IPsec connection; `connection` and `description` together identify a child, so keep descriptions unique per connection. Deleting the connection deletes its children too. A VTI pairs with a child through the same `reqid`; OPNsense does not check it. The apply needs IPsec enabled, as described for the IPsec connection. In the examples, replace `EXAMPLE_CONNECTION_UUID` with the `uuid` the connection example returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/IPsec/Swanctl.xml#children.child`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `connection` | ModelRelationField | yes |  |  |
| `reqid` | IntegerField |  |  |  |
| `esp_proposals` | IPsecProposalField, multiple | yes | `default` |  |
| `sha256_96` | BooleanField | yes | `0` |  |
| `start_action` | OptionField | yes | `start` | `none`, `trap\|start`, `route`, `start`, `trap` |
| `close_action` | OptionField | yes | `none` | `none`, `trap`, `start` |
| `dpd_action` | OptionField | yes | `clear` | `clear`, `trap`, `start` |
| `mode` | OptionField | yes | `tunnel` | `tunnel`, `transport`, `pass`, `drop` |
| `policies` | BooleanField | yes | `1` |  |
| `local_ts` | NetworkField |  |  |  |
| `remote_ts` | NetworkField |  |  |  |
| `rekey_time` | IntegerField | yes | `3600` |  |
| `replay_window` | IntegerField |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Add a tunnel child
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "child"
    lookup: ["connection", "description"]
    actions:
      add: "addChild"
      del: "delChild"
      get: "getChild"
      search: "searchChild"
      set: "setChild"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          connection: "EXAMPLE_CONNECTION_UUID"
          mode: "tunnel"
          local_ts: ["10.250.111.0/24"]
          remote_ts: ["10.250.116.0/24"]
          description: "routerops example child"

- name: Remove a child
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "child"
    lookup: ["connection", "description"]
    actions:
      add: "addChild"
      del: "delChild"
      get: "getChild"
      search: "searchChild"
      set: "setChild"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          connection: "EXAMPLE_CONNECTION_UUID"
          description: "routerops example child"
        state: "absent"
```

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

## IPsec local authentication

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `ipsec/connections` |
| Key | `local` |
| Actions | `add: addLocal`, `del: delLocal`, `get: getLocal`, `search: searchLocal`, `set: setLocal` |
| Lookup | `connection`, `description` |
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

`connection` is the uuid of an IPsec connection; `connection` and `description` together identify an entry, so keep descriptions unique per connection. Deleting the connection deletes this entry too. The apply needs IPsec enabled, as described for the IPsec connection. In the examples, replace `EXAMPLE_CONNECTION_UUID` with the `uuid` the connection example returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/IPsec/Swanctl.xml#locals.local`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `connection` | ModelRelationField | yes |  |  |
| `round` | IntegerField | yes | `0` |  |
| `auth` | OptionField | yes | `psk` | `psk`, `pubkey`, `eap-tls`, `eap-mschapv2`, `xauth-pam`, `eap-radius` |
| `id` | StrictTextField |  |  |  |
| `eap_id` | StrictTextField |  |  |  |
| `certs` | CertificateField, multiple |  |  |  |
| `pubkeys` | ModelRelationField, multiple |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Authenticate the local side with a pre-shared key
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "local"
    lookup: ["connection", "description"]
    actions:
      add: "addLocal"
      del: "delLocal"
      get: "getLocal"
      search: "searchLocal"
      set: "setLocal"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          connection: "EXAMPLE_CONNECTION_UUID"
          auth: "psk"
          id: "rt-example-local.routerops.test"
          description: "routerops example local"

- name: Remove the local authentication
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "local"
    lookup: ["connection", "description"]
    actions:
      add: "addLocal"
      del: "delLocal"
      get: "getLocal"
      search: "searchLocal"
      set: "setLocal"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          connection: "EXAMPLE_CONNECTION_UUID"
          description: "routerops example local"
        state: "absent"
```

## IPsec remote authentication

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `ipsec/connections` |
| Key | `remote` |
| Actions | `add: addRemote`, `del: delRemote`, `get: getRemote`, `search: searchRemote`, `set: setRemote` |
| Lookup | `connection`, `description` |
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

`connection` is the uuid of an IPsec connection; `connection` and `description` together identify an entry, so keep descriptions unique per connection. Deleting the connection deletes this entry too. The apply needs IPsec enabled, as described for the IPsec connection. In the examples, replace `EXAMPLE_CONNECTION_UUID` with the `uuid` the connection example returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/IPsec/Swanctl.xml#remotes.remote`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `connection` | ModelRelationField | yes |  |  |
| `round` | IntegerField | yes | `0` |  |
| `auth` | OptionField | yes | `psk` | `psk`, `pubkey`, `eap-tls`, `eap-mschapv2`, `xauth-pam`, `eap-radius` |
| `id` | StrictTextField |  |  |  |
| `eap_id` | StrictTextField |  |  |  |
| `groups` | AuthGroupField, multiple |  |  |  |
| `certs` | CertificateField, multiple |  |  |  |
| `cacerts` | CertificateField, multiple |  |  |  |
| `pubkeys` | ModelRelationField, multiple |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Authenticate the remote side with a pre-shared key
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "remote"
    lookup: ["connection", "description"]
    actions:
      add: "addRemote"
      del: "delRemote"
      get: "getRemote"
      search: "searchRemote"
      set: "setRemote"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          connection: "EXAMPLE_CONNECTION_UUID"
          auth: "psk"
          id: "rt-example-remote.routerops.test"
          description: "routerops example remote"

- name: Remove the remote authentication
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "ipsec/connections"
    key: "remote"
    lookup: ["connection", "description"]
    actions:
      add: "addRemote"
      del: "delRemote"
      get: "getRemote"
      search: "searchRemote"
      set: "setRemote"
    apply: "ipsec/service/reconfigure"
    items:
      - fields:
          connection: "EXAMPLE_CONNECTION_UUID"
          description: "routerops example remote"
        state: "absent"
```
