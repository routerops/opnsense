<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `unbound`

## ACL

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `unbound/settings` |
| Key | `acl` |
| Actions | `add: addAcl`, `del: delAcl`, `get: getAcl`, `search: searchAcl`, `set: setAcl` |
| Lookup | `name` |
| Item ids | `uuid` |
| Apply | `unbound/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Names are not unique; keep them unique, the lookup takes the name. Every apply restarts Unbound.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Unbound/Unbound.xml#acls.acl`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `name` | StrictTextField | yes |  |  |
| `action` | OptionField | yes | `allow` | `allow`, `deny`, `refuse`, `allow_snoop`, `deny_non_local`, `refuse_non_local` |
| `networks` | NetworkField, multiple | yes |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Allow a network
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "acl"
    lookup: ["name"]
    actions:
      add: "addAcl"
      del: "delAcl"
      get: "getAcl"
      search: "searchAcl"
      set: "setAcl"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          name: "routerops_example"
          action: "allow"
          networks: ["10.250.72.0/24"]
          description: "routerops example"

- name: Remove an ACL
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "acl"
    lookup: ["name"]
    actions:
      add: "addAcl"
      del: "delAcl"
      get: "getAcl"
      search: "searchAcl"
      set: "setAcl"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          name: "routerops_example"
        state: "absent"
```

## Query forward

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `unbound/settings` |
| Key | `dot` |
| Actions | `add: addForward`, `del: delForward`, `get: getForward`, `search: searchForward`, `set: setForward` |
| Lookup | `domain`, `server` |
| Item ids | `uuid` |
| Apply | `unbound/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Forward and DNS over TLS items share one list; the action name sets `type` and overwrites a sent one, so never send it, or every run shows a change. An empty `domain` forwards every query. Every apply restarts Unbound.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Unbound/Unbound.xml#dots.dot`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `type` | OptionField | yes | `dot` | `dot`, `forward` |
| `domain` | HostnameField |  |  |  |
| `server` | NetworkField | yes |  |  |
| `port` | PortField |  |  |  |
| `verify` | HostnameField |  |  |  |
| `forward_tcp_upstream` | BooleanField | yes | `0` |  |
| `forward_first` | BooleanField | yes | `0` |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Forward a domain
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "dot"
    lookup: ["domain", "server"]
    actions:
      add: "addForward"
      del: "delForward"
      get: "getForward"
      search: "searchForward"
      set: "setForward"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          domain: "routerops.test"
          server: "10.250.1.53"
          description: "routerops example"

- name: Remove a forward
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "dot"
    lookup: ["domain", "server"]
    actions:
      add: "addForward"
      del: "delForward"
      get: "getForward"
      search: "searchForward"
      set: "setForward"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          domain: "routerops.test"
          server: "10.250.1.53"
        state: "absent"
```

## Unbound general

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.settings` |
| Path | `unbound/settings` |
| Key | `unbound.general` |
| Actions | default |
| Lookup | - |
| Apply | `unbound/service/reconfigureGeneral` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Every apply restarts Unbound, so DNS stops answering for a moment. A save that changes `enabled` or `port` fails while another service uses the port.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Unbound/Unbound.xml#general`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `0` |  |
| `port` | PortField | yes | `53` |  |
| `stats` | BooleanField |  |  |  |
| `active_interface` | UnboundInterfaceField, multiple |  |  |  |
| `dnssec` | BooleanField |  |  |  |
| `dns64` | BooleanField |  |  |  |
| `dns64prefix` | NetworkField |  |  |  |
| `noarecords` | BooleanField |  |  |  |
| `regdhcp` | BooleanField |  |  |  |
| `regdhcpdomain` | TextField |  |  |  |
| `regdhcpstatic` | BooleanField |  |  |  |
| `noreglladdr6` | BooleanField |  |  |  |
| `noregrecords` | BooleanField |  |  |  |
| `txtsupport` | BooleanField |  |  |  |
| `cacheflush` | BooleanField |  |  |  |
| `safesearch` | BooleanField |  |  |  |
| `local_zone_type` | OptionField | yes | `transparent` | `transparent`, `always_nxdomain`, `always_refuse`, `always_transparent`, `deny`, `inform`, `inform_deny`, `nodefault`, `refuse`, `static`, `typetransparent` |
| `outgoing_interface` | UnboundInterfaceField, multiple |  |  |  |
| `enable_wpad` | BooleanField |  |  |  |

### Example

```yaml
- name: Enable TXT records for host overrides
  routerops.opnsense.settings:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "unbound.general"
    apply: "unbound/service/reconfigureGeneral"
    fields:
      txtsupport: true
```

## Host alias

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `unbound/settings` |
| Key | `alias` |
| Actions | `add: addHostAlias`, `del: delHostAlias`, `get: getHostAlias`, `search: searchHostAlias`, `set: setHostAlias` |
| Lookup | `host`, `hostname`, `domain` |
| Item ids | `uuid` |
| Apply | `unbound/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

`host` is the uuid of a host override; register it from the host override's outcome. The lookup includes `domain`, because an alias may set only a domain. Send `domain: ""` to take the host's domain; the lookup needs the field. In the examples, replace `HOST_OVERRIDE_UUID` with the `uuid` the example in the Host override section returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Unbound/Unbound.xml#aliases.alias`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `host` | ModelRelationField | yes |  |  |
| `hostname` | HostnameField |  |  |  |
| `domain` | TextField |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Add an alias for the example host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "alias"
    lookup: ["host", "hostname", "domain"]
    actions:
      add: "addHostAlias"
      del: "delHostAlias"
      get: "getHostAlias"
      search: "searchHostAlias"
      set: "setHostAlias"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          host: "HOST_OVERRIDE_UUID"
          hostname: "rt-example-alias"
          domain: ""
          description: "routerops example"

- name: Remove the alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "alias"
    lookup: ["host", "hostname", "domain"]
    actions:
      add: "addHostAlias"
      del: "delHostAlias"
      get: "getHostAlias"
      search: "searchHostAlias"
      set: "setHostAlias"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          host: "HOST_OVERRIDE_UUID"
          hostname: "rt-example-alias"
          domain: ""
        state: "absent"
```

## Host override

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `unbound/settings` |
| Key | `host` |
| Actions | `add: addHostOverride`, `del: delHostOverride`, `get: getHostOverride`, `search: searchHostOverride`, `set: setHostOverride` |
| Lookup | `hostname`, `domain`, `rr` |
| Item ids | `uuid` |
| Apply | `unbound/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-unbound` ("Services: Unbound", `api/unbound/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Do not send `aliases`: OPNsense adds and deletes alias items from it; manage them with the host alias area. The lookup includes `rr`, so an A and an AAAA record for one name are two items. Deleting a host override also deletes its aliases. Every apply restarts Unbound.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Unbound/Unbound.xml#hosts.host`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `hostname` | HostnameField |  |  |  |
| `domain` | TextField | yes |  |  |
| `rr` | OptionField | yes | `A` | `A`, `AAAA`, `MX`, `TXT` |
| `mxprio` | IntegerField |  |  |  |
| `mx` | HostnameField |  |  |  |
| `ttl` | IntegerField |  |  |  |
| `server` | NetworkField |  |  |  |
| `txtdata` | DescriptionField |  |  |  |
| `addptr` | BooleanField | yes | `1` |  |
| `aliases` | AliasReflector, not stored |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Add a host override
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "host"
    lookup: ["hostname", "domain", "rr"]
    actions:
      add: "addHostOverride"
      del: "delHostOverride"
      get: "getHostOverride"
      search: "searchHostOverride"
      set: "setHostOverride"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          hostname: "rt-example"
          domain: "routerops.test"
          rr: "A"
          server: "10.250.1.30"
          description: "routerops example"

- name: Remove a host override
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "host"
    lookup: ["hostname", "domain", "rr"]
    actions:
      add: "addHostOverride"
      del: "delHostOverride"
      get: "getHostOverride"
      search: "searchHostOverride"
      set: "setHostOverride"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          hostname: "rt-example"
          domain: "routerops.test"
          rr: "A"
        state: "absent"
```
