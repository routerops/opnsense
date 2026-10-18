<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `firewall`

## Firewall alias

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `firewall/alias` |
| Key | `alias` |
| Actions | default |
| Lookup | `name` |
| Apply | `firewall/alias/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `password` |
| Separators | `content`: `"\n"` |
| Privileges | `page-firewall-alias-edit` ("Firewall: Alias: Edit", `api/firewall/alias/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Firewall/Alias.xml#aliases.alias`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `name` | AliasNameField | yes |  |  |
| `type` | OptionField | yes | `alert` | `host`, `network`, `port`, `url`, `urltable`, `urljson`, `geoip`, `networkgroup`, `mac`, `asn`, `dynipv6host`, `authgroup`, `internal`, `external` |
| `path_expression` | TextField |  |  |  |
| `proto` | OptionField, multiple |  |  | `IPv4`, `IPv6` |
| `interface` | InterfaceField |  |  |  |
| `counters` | BooleanField |  |  |  |
| `updatefreq` | NumericField |  |  |  |
| `content` | AliasContentField |  |  |  |
| `password` (secret) | TextField |  |  |  |
| `username` | TextField |  |  |  |
| `authtype` | OptionField |  |  | `Basic`, `Bearer`, `Header` |
| `expire` | IntegerField |  |  |  |
| `categories` | ModelRelationField, multiple |  |  |  |
| `current_items` | IntegerField, not stored |  |  |  |
| `last_updated` | TextField, not stored |  |  |  |
| `eval_nomatch` | IntegerField, not stored |  |  |  |
| `eval_match` | IntegerField, not stored |  |  |  |
| `in_block_p` | IntegerField, not stored |  |  |  |
| `in_block_b` | IntegerField, not stored |  |  |  |
| `in_pass_p` | IntegerField, not stored |  |  |  |
| `in_pass_b` | IntegerField, not stored |  |  |  |
| `out_block_p` | IntegerField, not stored |  |  |  |
| `out_block_b` | IntegerField, not stored |  |  |  |
| `out_pass_p` | IntegerField, not stored |  |  |  |
| `out_pass_b` | IntegerField, not stored |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Keep a host alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/alias"
    key: "alias"
    lookup: ["name"]
    separators:
      content: "\n"
    secret_fields: ["password"]
    apply: "firewall/alias/reconfigure"
    items:
      - fields:
          name: "web_servers"
          type: "host"
          content: ["192.0.2.21", "192.0.2.22"]
          description: "Web servers"

- name: Keep a port alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/alias"
    key: "alias"
    lookup: ["name"]
    separators:
      content: "\n"
    secret_fields: ["password"]
    apply: "firewall/alias/reconfigure"
    items:
      - fields:
          name: "web_ports"
          type: "port"
          content: ["80", "443"]
          description: "Web ports"

- name: Read a built-in alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/alias"
    key: "alias"
    lookup: ["name"]
    separators:
      content: "\n"
    secret_fields: ["password"]
    apply: "firewall/alias/reconfigure"
    return_fields: ["type"]
    items:
      - fields:
          name: "bogons"
        state: "query"
```

## Firewall destination NAT

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `firewall/d_nat` |
| Key | `rule` |
| Actions | `add: addRule`, `del: delRule`, `get: getRule`, `search: searchRule`, `set: setRule` |
| Lookup | `descr` |
| Apply | `firewall/d_nat/apply` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-firewall-nat-portforward-edit` ("Firewall: NAT: Destination NAT", `api/firewall/d_nat/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Firewall/DNat.xml#rule`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `sequence` | DNatSequenceField | yes |  |  |
| `disabled` | BooleanField |  |  |  |
| `nordr` | BooleanField |  |  |  |
| `interface` | InterfaceField, multiple |  |  |  |
| `ipprotocol` | OptionField |  |  | `inet`, `inet6`, `inet46` |
| `protocol` | ProtocolField |  |  |  |
| `source.network` | NetworkMappedField |  |  |  |
| `source.address` | NetworkMappedField, not stored |  |  |  |
| `source.port` | PortMappedField |  |  |  |
| `source.not` | BooleanField |  |  |  |
| `destination.network` | NetworkMappedField |  |  |  |
| `destination.address` | NetworkMappedField, not stored |  |  |  |
| `destination.port` | PortMappedField |  |  |  |
| `destination.not` | BooleanField |  |  |  |
| `target` | NetworkAliasField |  |  |  |
| `local-port` | PortField |  |  |  |
| `poolopts` | OptionField |  |  | `round-robin`, `round-robin sticky-address`, `random`, `random sticky-address`, `source-hash`, `bitmask` |
| `log` | BooleanField |  |  |  |
| `category` | CategoryField, multiple |  |  |  |
| `categories` | CategoryMapField, not stored |  |  |  |
| `descr` | DescriptionField |  |  |  |
| `tag` | StrictTextField |  |  |  |
| `tagged` | StrictTextField |  |  |  |
| `nosync` | BooleanField |  |  |  |
| `natreflection` | OptionField |  |  | `purenat`, `disable` |
| `pass` | OptionField |  |  | `pass`, `rule` |
| `audit` | JsonAuditField |  |  |  |
| `associated-rule-id` | DNatAssociatedRuleField |  |  |  |
| `created` | JsonAuditField, not stored |  |  |  |

### Examples

```yaml
- name: Forward port 8080 on WAN to a LAN web server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/d_nat"
    key: "rule"
    lookup: ["descr"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/d_nat/apply"
    items:
      - fields:
          interface: "wan"
          protocol: "tcp"
          destination:
            network: "wanip"
            port: "8080"
          target: "10.250.1.50"
          local-port: "80"
          descr: "routerops example web"

- name: Remove a port forward
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/d_nat"
    key: "rule"
    lookup: ["descr"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/d_nat/apply"
    items:
      - fields:
          descr: "routerops example web"
        state: "absent"
```

## Firewall filter rule

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `firewall/filter` |
| Key | `rule` |
| Actions | `add: addRule`, `del: delRule`, `get: getRule`, `search: searchRule`, `set: setRule` |
| Lookup | `description` |
| Apply | `firewall/filter/apply` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-filter-api` ("Firewall: Rules [new]", `api/firewall/filter/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Firewall/Filter.xml#rules.rule`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `statetype` | OptionField | yes | `keep` | `keep`, `sloppy`, `modulate`, `synproxy`, `none` |
| `state-policy` | OptionField |  |  | `if-bound`, `floating` |
| `sequence` | FilterSequenceField | yes | `1` |  |
| `sort_order` | TextField, not stored |  |  |  |
| `prio_group` | TextField, not stored |  |  |  |
| `action` | OptionField | yes | `pass` | `pass`, `block`, `reject` |
| `quick` | BooleanField | yes | `1` |  |
| `interfacenot` | BooleanField | yes | `0` |  |
| `interface` | InterfaceField, multiple |  |  |  |
| `received-on-not` | BooleanField | yes | `0` |  |
| `received-on` | InterfaceField, multiple |  |  |  |
| `direction` | OptionField | yes | `in` | `in`, `out`, `any` |
| `ipprotocol` | OptionField | yes | `inet` | `inet`, `inet6`, `inet46` |
| `protocol` | ProtocolField | yes | `any` |  |
| `icmptype` | OptionField, multiple |  |  | `echoreq`, `echorep`, `unreach`, `redir`, `routeradv`, `routersol`, `timex`, `paramprob`, `timereq`, `timerep`, `photuris`, `squench`, `althost`, `inforeq`, `inforep`, `maskreq`, `maskrep`, `trace`, `dataconv`, `mobredir`, `ipv6-where`, `ipv6-here`, `mobregreq`, `mobregrep`, `skip` |
| `icmp6type` | OptionField, multiple |  |  | `1`, `2`, `3`, `4`, `128`, `129`, `130`, `131`, `132`, `133`, `134`, `135`, `136`, `137`, `138`, `139`, `140`, `200`, `201` |
| `source_net` | NetworkAliasField, multiple | yes | `any` |  |
| `source_not` | BooleanField | yes | `0` |  |
| `source_port` | PortField |  |  |  |
| `destination_net` | NetworkAliasField, multiple | yes | `any` |  |
| `destination_not` | BooleanField | yes | `0` |  |
| `destination_port` | PortField |  |  |  |
| `divert-to` | JsonKeyValueStoreField |  |  |  |
| `gateway` | JsonKeyValueStoreField |  |  |  |
| `replyto` | JsonKeyValueStoreField |  |  |  |
| `disablereplyto` | BooleanField | yes | `0` |  |
| `log` | BooleanField | yes | `0` |  |
| `allowopts` | BooleanField | yes | `0` |  |
| `nosync` | BooleanField | yes | `0` |  |
| `nopfsync` | BooleanField | yes | `0` |  |
| `statetimeout` | IntegerField |  |  |  |
| `udp-first` | IntegerField |  |  |  |
| `udp-multiple` | IntegerField |  |  |  |
| `udp-single` | IntegerField |  |  |  |
| `max-src-nodes` | IntegerField |  |  |  |
| `max-src-states` | IntegerField |  |  |  |
| `max-src-conn` | IntegerField |  |  |  |
| `max` | IntegerField |  |  |  |
| `max-src-conn-rate` | IntegerField |  |  |  |
| `max-src-conn-rates` | IntegerField |  |  |  |
| `max-pkt-rate-number` | IntegerField |  |  |  |
| `max-pkt-rate-seconds` | IntegerField |  |  |  |
| `overload` | ModelRelationField |  |  |  |
| `adaptivestart` | IntegerField |  |  |  |
| `adaptiveend` | IntegerField |  |  |  |
| `prio` | OptionField |  |  | `1`, `0`, `2`, `3`, `4`, `5`, `6`, `7` |
| `set-prio` | OptionField |  |  | `1`, `0`, `2`, `3`, `4`, `5`, `6`, `7` |
| `set-prio-low` | OptionField |  |  | `1`, `0`, `2`, `3`, `4`, `5`, `6`, `7` |
| `tag` | StrictTextField |  |  |  |
| `tagged` | StrictTextField |  |  |  |
| `tcpflags1` | OptionField, multiple |  |  | `syn`, `ack`, `fin`, `rst`, `psh`, `urg`, `ece`, `cwr` |
| `tcpflags2` | OptionField, multiple |  |  | `syn`, `ack`, `fin`, `rst`, `psh`, `urg`, `ece`, `cwr` |
| `tcpflags_any` | BooleanField |  |  |  |
| `categories` | ModelRelationField, multiple |  |  |  |
| `sched` | ScheduleField |  |  |  |
| `tos` | TosField |  |  |  |
| `shaper1` | ModelRelationField |  |  |  |
| `shaper2` | ModelRelationField |  |  |  |
| `description` | DescriptionField |  |  |  |
| `audit` | JsonAuditField |  |  |  |

### Examples

```yaml
- name: Allow HTTPS to the firewall from LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/filter"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/filter/apply"
    items:
      - fields:
          interface: "lan"
          protocol: "TCP"
          source_net: "lan"
          destination_net: "(self)"
          destination_port: "443"
          description: "routerops example https"

- name: Block a host on LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/filter"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/filter/apply"
    items:
      - fields:
          action: "block"
          source_net: "10.250.1.99"
          description: "routerops example block"

- name: Remove a filter rule
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/filter"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/filter/apply"
    items:
      - fields:
          description: "routerops example block"
        state: "absent"
```

## Firewall one-to-one NAT

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `firewall/one_to_one` |
| Key | `rule` |
| Actions | `add: addRule`, `del: delRule`, `get: getRule`, `search: searchRule`, `set: setRule` |
| Lookup | `description` |
| Apply | `firewall/one_to_one/apply` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-firewall-nat-1-1-edit` ("Firewall: NAT: 1:1", `api/firewall/one_to_one/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Firewall/Filter.xml#onetoone.rule`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `log` | BooleanField | yes | `0` |  |
| `sequence` | FilterSequenceField | yes | `1` |  |
| `sort_order` | TextField, not stored |  |  |  |
| `prio_group` | TextField, not stored |  |  |  |
| `interface` | InterfaceField | yes | `wan` |  |
| `type` | OptionField | yes | `binat` | `binat`, `nat` |
| `source_net` | NetworkAliasField | yes |  |  |
| `source_not` | BooleanField | yes | `0` |  |
| `destination_net` | NetworkAliasField | yes | `any` |  |
| `destination_not` | BooleanField | yes | `0` |  |
| `external` | NetworkField | yes |  |  |
| `natreflection` | OptionField |  |  | ``, `enable`, `disable` |
| `categories` | ModelRelationField, multiple |  |  |  |
| `description` | DescriptionField |  |  |  |
| `audit` | JsonAuditField |  |  |  |

### Examples

```yaml
- name: Map a LAN host to a WAN address
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/one_to_one"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/one_to_one/apply"
    items:
      - fields:
          source_net: "10.250.1.50"
          external: "10.250.0.50"
          description: "routerops example one"

- name: Keep only the listed one-to-one rules
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/one_to_one"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/one_to_one/apply"
    purge: true
    items:
      - fields:
          source_net: "10.250.1.50"
          external: "10.250.0.50"
          description: "routerops example one"
      - fields:
          source_net: "10.250.1.51"
          external: "10.250.0.51"
          description: "routerops example two"

- name: Remove a one-to-one rule
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/one_to_one"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/one_to_one/apply"
    items:
      - fields:
          description: "routerops example two"
        state: "absent"
```

## Firewall source NAT rule

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `firewall/source_nat` |
| Key | `rule` |
| Actions | `add: addRule`, `del: delRule`, `get: getRule`, `search: searchRule`, `set: setRule` |
| Lookup | `description` |
| Apply | `firewall/source_nat/apply` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-filter-snat-api` ("Firewall: NAT: Source NAT", `api/firewall/source_nat/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

OPNsense lists source NAT rules only in the outbound NAT mode `hybrid` or `advanced` (default `automatic`); set the mode with the outbound NAT mode entry first, or every run adds a duplicate rule and `absent` finds nothing.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Firewall/Filter.xml#snatrules.rule`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `1` |  |
| `nonat` | BooleanField | yes | `0` |  |
| `nosync` | BooleanField | yes | `0` |  |
| `sequence` | FilterSequenceField | yes | `1` |  |
| `sort_order` | TextField, not stored |  |  |  |
| `prio_group` | TextField, not stored |  |  |  |
| `interface` | InterfaceField | yes |  |  |
| `ipprotocol` | OptionField | yes | `inet` | `inet`, `inet6` |
| `protocol` | ProtocolField | yes | `any` |  |
| `source_net` | NetworkAliasField | yes | `any` |  |
| `source_not` | BooleanField | yes | `0` |  |
| `source_port` | PortField |  |  |  |
| `destination_net` | NetworkAliasField | yes | `any` |  |
| `destination_not` | BooleanField | yes | `0` |  |
| `destination_port` | PortField |  |  |  |
| `target` | NetworkAliasField |  |  |  |
| `target_port` | PortField |  |  |  |
| `poolopts` | OptionField |  |  | `round-robin`, `round-robin sticky-address`, `random`, `random sticky-address`, `source-hash`, `bitmask` |
| `poolopts_sourcehashkey` | StrictTextField |  |  |  |
| `staticnatport` | BooleanField |  |  |  |
| `log` | BooleanField | yes | `0` |  |
| `categories` | ModelRelationField, multiple |  |  |  |
| `tag` | StrictTextField |  |  |  |
| `tagged` | StrictTextField |  |  |  |
| `endpoint-independent` | BooleanField |  |  |  |
| `description` | DescriptionField |  |  |  |
| `audit` | JsonAuditField |  |  |  |

### Examples

```yaml
- name: Translate a LAN subnet on WAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/source_nat"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/source_nat/apply"
    items:
      - fields:
          interface: "wan"
          source_net: "10.250.1.0/24"
          description: "routerops example lan"

- name: Remove a source NAT rule
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/source_nat"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/source_nat/apply"
    items:
      - fields:
          description: "routerops example lan"
        state: "absent"
```

## Firewall outbound NAT mode

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.settings` |
| Path | `firewall/source_nat` |
| Key | `filter.general` |
| Actions | default |
| Lookup | - |
| Apply | `firewall/source_nat/apply` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-filter-snat-api` ("Firewall: NAT: Source NAT", `api/firewall/source_nat/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Firewall/Filter.xml#general`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `snat_mode` | SNatModeField, not stored | yes | `automatic` | `automatic`, `hybrid`, `advanced`, `disabled` |

### Example

```yaml
- name: Use hybrid outbound NAT
  routerops.opnsense.settings:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/source_nat"
    key: "filter.general"
    apply: "firewall/source_nat/apply"
    fields:
      snat_mode: "hybrid"
```
