<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `dnsmasq`

## Dnsmasq domain override

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `dnsmasq/settings` |
| Key | `domainoverride` |
| Actions | `add: addDomain`, `del: delDomain`, `get: getDomain`, `search: searchDomain`, `set: setDomain` |
| Lookup | `domain`, `ip`, `ipset` |
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

The lookup includes `ip` and `ipset`, so one domain can go to several servers or feed several aliases; send the unused one as `""`. With `ip` and `ipset` empty, Dnsmasq answers the domain from its hosts and leases only and never forwards it; with only `ipset` set, the domain is forwarded as usual and its addresses go into the alias. `!` is stored as empty and shows a change on every run. Every apply also reloads the firewall rules.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Dnsmasq/Dnsmasq.xml#domainoverrides`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `sequence` | AutoNumberField | yes | `1` |  |
| `domain` | HostnameField | yes |  |  |
| `ipset` | ModelRelationField |  |  |  |
| `srcip` | NetworkField |  |  |  |
| `port` | PortField |  |  |  |
| `ip` | DomainIPField |  |  |  |
| `descr` | TextField |  |  |  |

### Examples

```yaml
- name: Send a domain to another server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "domainoverride"
    lookup: ["domain", "ip", "ipset"]
    actions:
      add: "addDomain"
      del: "delDomain"
      get: "getDomain"
      search: "searchDomain"
      set: "setDomain"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          domain: "example.routerops.test"
          ip: "10.250.1.53"
          ipset: ""
          descr: "routerops example"

- name: Remove a domain override
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "domainoverride"
    lookup: ["domain", "ip", "ipset"]
    actions:
      add: "addDomain"
      del: "delDomain"
      get: "getDomain"
      search: "searchDomain"
      set: "setDomain"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          domain: "example.routerops.test"
          ip: "10.250.1.53"
          ipset: ""
        state: "absent"
```

## Dnsmasq general

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.settings` |
| Path | `dnsmasq/settings` |
| Key | `dnsmasq` |
| Actions | default |
| Lookup | - |
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

Unbound holds port 53, and OPNsense runs Dnsmasq on port 53053 by default; a save that moves Dnsmasq onto a port another service uses fails. Send `port: 0` to run Dnsmasq for DHCP only. Every apply also reloads the firewall rules.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Dnsmasq/Dnsmasq.xml`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enable` | BooleanField |  |  |  |
| `regdhcp` | BooleanField |  |  |  |
| `regdhcpstatic` | BooleanField |  |  |  |
| `dhcpfirst` | BooleanField |  |  |  |
| `strict_order` | BooleanField |  |  |  |
| `domain_needed` | BooleanField |  |  |  |
| `no_private_reverse` | BooleanField |  |  |  |
| `no_resolv` | BooleanField |  |  |  |
| `log_queries` | BooleanField |  |  |  |
| `no_hosts` | BooleanField |  |  |  |
| `expand_hosts` | BooleanField |  |  |  |
| `strictbind` | BooleanField |  |  |  |
| `dnssec` | BooleanField |  |  |  |
| `regdhcpdomain` | HostnameField |  |  |  |
| `interface` | InterfaceField, multiple |  |  |  |
| `port` | IntegerField |  |  |  |
| `dns_port` | IntegerField, not stored |  |  |  |
| `dns_forward_max` | IntegerField |  |  |  |
| `cache_size` | IntegerField |  |  |  |
| `local_ttl` | IntegerField |  |  |  |
| `add_mac` | OptionField |  |  | `standard`, `base64`, `text` |
| `add_subnet` | BooleanField |  |  |  |
| `strip_subnet` | BooleanField |  |  |  |
| `dhcp.no_interface` | InterfaceField, multiple |  |  |  |
| `dhcp.fqdn` | BooleanField | yes | `1` |  |
| `dhcp.domain` | HostnameField |  |  |  |
| `dhcp.local` | BooleanField | yes | `1` |  |
| `dhcp.lease_max` | IntegerField |  |  |  |
| `dhcp.authoritative` | BooleanField |  |  |  |
| `dhcp.default_fw_rules` | BooleanField | yes | `1` |  |
| `dhcp.reply_delay` | IntegerField |  |  |  |
| `dhcp.enable_ra` | BooleanField |  |  |  |
| `dhcp.host_ping` | BooleanField | yes | `1` |  |
| `dhcp.nosync` | BooleanField |  |  |  |
| `dhcp.log_dhcp` | BooleanField |  |  |  |
| `dhcp.log_quiet` | BooleanField |  |  |  |
| `no_ident` | BooleanField | yes | `1` |  |

### Example

```yaml
- name: Raise the lease limit
  routerops.opnsense.settings:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "dnsmasq"
    apply: "dnsmasq/service/reconfigure"
    fields:
      dhcp:
        lease_max: 2000
```

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

## Dnsmasq DHCP option

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `dnsmasq/settings` |
| Key | `option` |
| Actions | `add: addOption`, `del: delOption`, `get: getOption`, `search: searchOption`, `set: setOption` |
| Lookup | `description` |
| Item ids | `uuid` |
| Apply | `dnsmasq/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | `type` |
| Secret fields | - |
| Separators | - |
| Privileges | `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings", `api/dnsmasq/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

OPNsense clears the fields that do not fit `type` on a write that sends it, as the GUI always does, so the module sends `type` on every update. `type: set` clears `set_tag`, and `type: match` clears `tag`, `interface` and `force`; send only the fields that fit, or every run shows a change. `option` takes the DHCP option number (`6` is dns-server). Descriptions identify an option; keep them unique. Options made in the GUI often have no description, and two of those collide, so give each one a description before managing it here.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Dnsmasq/Dnsmasq.xml#dhcp_options`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `type` | OptionField | yes | `set` | `set`, `match` |
| `option` | JsonKeyValueStoreField |  |  | `optgroup1`, `optgroup2`, `optgroup3` |
| `option6` | JsonKeyValueStoreField |  |  | `optgroup1`, `optgroup2`, `optgroup3` |
| `interface` | InterfaceField |  |  |  |
| `tag` | ModelRelationField, multiple |  |  |  |
| `set_tag` | ModelRelationField |  |  |  |
| `value` | StrictTextField |  |  |  |
| `force` | BooleanField |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Hand out the LAN DNS server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "option"
    lookup: ["description"]
    actions:
      add: "addOption"
      del: "delOption"
      get: "getOption"
      search: "searchOption"
      set: "setOption"
    always_send: ["type"]
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          type: "set"
          option: "6"
          interface: "lan"
          value: "10.250.1.1"
          description: "routerops example"

- name: Remove a DHCP option
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "option"
    lookup: ["description"]
    actions:
      add: "addOption"
      del: "delOption"
      get: "getOption"
      search: "searchOption"
      set: "setOption"
    always_send: ["type"]
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          description: "routerops example"
        state: "absent"
```

## Dnsmasq DHCP range

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `dnsmasq/settings` |
| Key | `range` |
| Actions | `add: addRange`, `del: delRange`, `get: getRange`, `search: searchRange`, `set: setRange` |
| Lookup | `interface`, `start_addr` |
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

A range serves DHCP once Dnsmasq is enabled, which it is by default, and listens on the range's interface, by default only `lan`. With `dhcp.default_fw_rules` on, the firewall opens DHCP on the listen interfaces, or on every range interface when Dnsmasq listens on all. Every apply also reloads the firewall rules.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Dnsmasq/Dnsmasq.xml#dhcp_ranges`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `interface` | InterfaceField |  |  |  |
| `set_tag` | ModelRelationField |  |  |  |
| `start_addr` | RangeAddressField | yes |  |  |
| `end_addr` | RangeAddressField |  |  |  |
| `subnet_mask` | NetworkField |  |  |  |
| `constructor` | InterfaceField |  |  |  |
| `mode` | OptionField, multiple |  |  | `static` |
| `prefix_len` | IntegerField |  |  |  |
| `lease_time` | IntegerField |  |  |  |
| `domain_type` | OptionField | yes | `range` | `interface`, `range` |
| `domain` | HostnameField |  |  |  |
| `nosync` | BooleanField |  |  |  |
| `ra_mode` | OptionField, multiple |  |  | `ra-only`, `slaac`, `ra-names`, `ra-stateless`, `ra-advrouter`, `off-link` |
| `ra_priority` | OptionField |  |  | `high`, `low` |
| `ra_mtu` | IntegerField |  |  |  |
| `ra_interval` | IntegerField |  |  |  |
| `ra_router_lifetime` | IntegerField |  |  |  |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Add a DHCP range on LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "range"
    lookup: ["interface", "start_addr"]
    actions:
      add: "addRange"
      del: "delRange"
      get: "getRange"
      search: "searchRange"
      set: "setRange"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          interface: "lan"
          start_addr: "10.250.1.200"
          end_addr: "10.250.1.219"
          description: "routerops example"

- name: Remove a DHCP range
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "range"
    lookup: ["interface", "start_addr"]
    actions:
      add: "addRange"
      del: "delRange"
      get: "getRange"
      search: "searchRange"
      set: "setRange"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          interface: "lan"
          start_addr: "10.250.1.200"
        state: "absent"
```
