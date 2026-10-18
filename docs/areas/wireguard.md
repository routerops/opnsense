<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `wireguard`

## WireGuard peer

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `wireguard/client` |
| Key | `client` |
| Actions | `add: addClient`, `del: delClient`, `get: getClient`, `search: searchClient`, `set: setClient` |
| Lookup | `name` |
| Item ids | `uuid` |
| Apply | `wireguard/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | `tunneladdress` |
| Always sent | `servers` |
| Secret fields | `psk` |
| Separators | - |
| Privileges | `page-wireguard-config` ("VPN: WireGuard: Configuration", `api/wireguard/client/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

`servers` lists the uuids of the servers the peer belongs to. OPNsense reads it on every write and drops the peer from every server when it is missing, so the module always sends it; list it in every present item. `tunneladdress` keeps the order you send. `keepalive` takes 1 to 65535; leave it out for none. The pre-shared key is readable through the API; it is masked in the diff and the return values. Names identify a peer; keep them unique. In the examples, replace `EXAMPLE_PEER_PUBKEY` with the peer's public key and `SERVER_UUID` with the `uuid` the example in the WireGuard server section returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Wireguard/Client.xml#clients.client`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `name` | TextField | yes |  |  |
| `pubkey` | Base64Field | yes |  |  |
| `psk` (secret) | Base64Field |  |  |  |
| `tunneladdress` | NetworkField | yes |  |  |
| `serveraddress` | HostnameField |  |  |  |
| `serverport` | PortField |  |  |  |
| `endpoint` | IPPortField, not stored |  |  |  |
| `keepalive` | IntegerField |  |  |  |
| `servers` | ModelRelationField, multiple, not stored |  |  |  |
| `privkey` | Base64Field |  |  |  |

### Examples

```yaml
- name: Add a WireGuard peer
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "wireguard/client"
    key: "client"
    lookup: ["name"]
    actions:
      add: "addClient"
      del: "delClient"
      get: "getClient"
      search: "searchClient"
      set: "setClient"
    ordered_fields: ["tunneladdress"]
    secret_fields: ["psk"]
    always_send: ["servers"]
    apply: "wireguard/service/reconfigure"
    items:
      - fields:
          name: "rt-example-peer"
          pubkey: "EXAMPLE_PEER_PUBKEY"
          tunneladdress: ["10.250.92.2/32"]
          servers: ["SERVER_UUID"]

- name: Remove a WireGuard peer
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "wireguard/client"
    key: "client"
    lookup: ["name"]
    actions:
      add: "addClient"
      del: "delClient"
      get: "getClient"
      search: "searchClient"
      set: "setClient"
    ordered_fields: ["tunneladdress"]
    secret_fields: ["psk"]
    always_send: ["servers"]
    apply: "wireguard/service/reconfigure"
    items:
      - fields:
          name: "rt-example-peer"
        state: "absent"
```

## WireGuard server

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `wireguard/server` |
| Key | `server` |
| Actions | `add: addServer`, `del: delServer`, `get: getServer`, `search: searchServer`, `set: setServer` |
| Lookup | `name` |
| Item ids | `uuid` |
| Apply | `wireguard/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `privkey` |
| Separators | - |
| Privileges | `page-wireguard-config` ("VPN: WireGuard: Configuration", `api/wireguard/server/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Create the key pair with `wireguard/server/key_pair` and send `privkey` and `pubkey`; OPNsense does not derive the public key. Attach peers through the peer's `servers`, never through `peers`. OPNsense numbers servers itself (`instance`, interface `wgN`). WireGuard runs only after `wireguard/general` `enabled` is set; the apply answers `ok` even when the configuration fails. The private key is readable through the API; it is masked in the diff and the return values. Names identify a server; keep them unique. In the examples, replace `EXAMPLE_SERVER_PRIVKEY` and `EXAMPLE_SERVER_PUBKEY` with a generated key pair.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Wireguard/Server.xml#servers.server`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `name` | TextField | yes |  |  |
| `instance` | AutoNumberField | yes |  |  |
| `pubkey` | Base64Field |  |  |  |
| `privkey` (secret) | Base64Field | yes |  |  |
| `port` | PortField |  |  |  |
| `mtu` | IntegerField |  |  |  |
| `dns` | NetworkField |  |  |  |
| `tunneladdress` | NetworkField |  |  |  |
| `disableroutes` | BooleanField | yes | `0` |  |
| `gateway` | NetworkField |  |  |  |
| `carp_depend_on` | VirtualIPField |  |  |  |
| `peers` | ModelRelationField, multiple |  |  |  |
| `debug` | BooleanField | yes | `0` |  |
| `cnfFilename` | TextField, not stored |  |  |  |
| `statFilename` | TextField, not stored |  |  |  |
| `interface` | TextField, not stored |  |  |  |
| `endpoint` | TextField |  |  |  |
| `peer_dns` | TextField |  |  |  |
| `allowed_ips` | TextField |  |  |  |

### Examples

```yaml
- name: Add a WireGuard server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "wireguard/server"
    key: "server"
    lookup: ["name"]
    actions:
      add: "addServer"
      del: "delServer"
      get: "getServer"
      search: "searchServer"
      set: "setServer"
    secret_fields: ["privkey"]
    apply: "wireguard/service/reconfigure"
    items:
      - fields:
          name: "rt-example"
          privkey: "EXAMPLE_SERVER_PRIVKEY"
          pubkey: "EXAMPLE_SERVER_PUBKEY"
          port: "51822"
          tunneladdress: ["10.250.92.1/24"]

- name: Remove a WireGuard server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "wireguard/server"
    key: "server"
    lookup: ["name"]
    actions:
      add: "addServer"
      del: "delServer"
      get: "getServer"
      search: "searchServer"
      set: "setServer"
    secret_fields: ["privkey"]
    apply: "wireguard/service/reconfigure"
    items:
      - fields:
          name: "rt-example"
        state: "absent"
```
