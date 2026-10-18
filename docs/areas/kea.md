<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `kea`

## Kea DHCPv4 general

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.settings` |
| Path | `kea/dhcpv4` |
| Key | `dhcpv4.general` |
| Actions | default |
| Lookup | - |
| Apply | `kea/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", `api/kea/dhcpv4/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Kea serves DHCP only with `enabled: true` and at least one entry in `interfaces`. A save rewrites the router, DNS and NTP options of every subnet that collects them automatically and lies on an interface.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Kea/KeaDhcpv4.xml#general`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `enabled` | BooleanField | yes | `0` |  |
| `manual_config` | BooleanField |  |  |  |
| `interfaces` | InterfaceField, multiple |  |  |  |
| `service_sockets_max_retries` | IntegerField |  |  |  |
| `service_sockets_retry_wait_time` | IntegerField |  |  |  |
| `valid_lifetime` | IntegerField | yes | `4000` |  |
| `decline_probation_period` | IntegerField |  |  |  |
| `fwrules` | BooleanField | yes | `1` |  |
| `dhcp_socket_type` | OptionField | yes | `raw` | `udp`, `raw` |
| `compatibility` | OptionField, multiple |  |  | `exclude-first-last-24`, `ignore-dhcp-server-identifier`, `ignore-rai-link-selection`, `lenient-option-parsing` |

### Example

```yaml
- name: Set the default lease time
  routerops.opnsense.settings:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "dhcpv4.general"
    apply: "kea/service/reconfigure"
    fields:
      valid_lifetime: 7200
```

## DHCPv4 reservation

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `kea/dhcpv4` |
| Key | `reservation` |
| Actions | `add: addReservation`, `del: delReservation`, `get: getReservation`, `search: searchReservation`, `set: setReservation` |
| Lookup | `subnet`, `hw_address`, `client_id` |
| Item ids | `uuid` |
| Apply | `kea/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", `api/kea/dhcpv4/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

`subnet` is the uuid of a subnet; register it from the subnet's outcome. Reservations hold MAC addresses and host names, which can be personal data, and `--diff` prints them. OPNsense stores `hw_address` as sent but checks it for duplicates regardless of case, so send it in the same case on every run; a run in another case fails with "Duplicate entry exists." A reservation sets either `hw_address` or `client_id`; send the other one as `""`, because the lookup needs both. In the examples, replace `SUBNET_UUID` with the `uuid` the subnet example returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Kea/KeaDhcpv4.xml#reservations.reservation`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `subnet` | ModelRelationField | yes |  |  |
| `ip_address` | NetworkField |  |  |  |
| `hw_address` | MacAddressField |  |  |  |
| `client_id` | TextField |  |  |  |
| `hostname` | HostnameField |  |  |  |
| `description` | DescriptionField |  |  |  |
| `next_server` | NetworkField |  |  |  |
| `option_data.domain_name_servers` | NetworkField |  |  |  |
| `option_data.domain_search` | HostnameField |  |  |  |
| `option_data.routers` | NetworkField |  |  |  |
| `option_data.static_routes` | KeaStaticRoutesField |  |  |  |
| `option_data.classless_static_route` | KeaClasslessStaticRouteField |  |  |  |
| `option_data.domain_name` | HostnameField |  |  |  |
| `option_data.ntp_servers` | NetworkField |  |  |  |
| `option_data.time_servers` | NetworkField |  |  |  |
| `option_data.tftp_server_name` | TextField |  |  |  |
| `option_data.boot_file_name` | TextField |  |  |  |
| `option` | ModelRelationField, multiple |  |  |  |

### Examples

```yaml
- name: Reserve an address
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "reservation"
    lookup: ["subnet", "hw_address", "client_id"]
    actions:
      add: "addReservation"
      del: "delReservation"
      get: "getReservation"
      search: "searchReservation"
      set: "setReservation"
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "SUBNET_UUID"
          hw_address: "02:00:00:00:69:01"
          client_id: ""
          ip_address: "10.250.69.10"
          hostname: "rt-example"
          description: "routerops example"

- name: Remove a reservation
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "reservation"
    lookup: ["subnet", "hw_address", "client_id"]
    actions:
      add: "addReservation"
      del: "delReservation"
      get: "getReservation"
      search: "searchReservation"
      set: "setReservation"
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "SUBNET_UUID"
          hw_address: "02:00:00:00:69:01"
          client_id: ""
        state: "absent"
```

## DHCPv4 subnet

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `kea/dhcpv4` |
| Key | `subnet4` |
| Actions | `add: addSubnet`, `del: delSubnet`, `get: getSubnet`, `search: searchSubnet`, `set: setSubnet` |
| Lookup | `subnet` |
| Item ids | `uuid` |
| Apply | `kea/service/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `ddns_domain_key_secret` |
| Separators | `pools`: `"\n"` |
| Privileges | `page-dhcp-kea-v4` ("Services: DHCP: Kea(v4)", `api/kea/dhcpv4/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Leave the `option_data` fields unset while `option_data_autocollect` is on; OPNsense fills them on every general save. A subnet a reservation uses cannot be deleted; delete the reservations first. `pools` takes one `start-end` range or CIDR per entry.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Kea/KeaDhcpv4.xml#subnets.subnet4`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `subnet_id` | AutoNumberField | yes |  |  |
| `subnet` | NetworkField | yes |  |  |
| `valid_lifetime` | IntegerField |  |  |  |
| `next_server` | NetworkField |  |  |  |
| `option_data_autocollect` | BooleanField | yes | `1` |  |
| `option_data.domain_name_servers` | NetworkField |  |  |  |
| `option_data.domain_search` | HostnameField |  |  |  |
| `option_data.routers` | NetworkField |  |  |  |
| `option_data.static_routes` | KeaStaticRoutesField |  |  |  |
| `option_data.classless_static_route` | KeaClasslessStaticRouteField |  |  |  |
| `option_data.domain_name` | HostnameField |  |  |  |
| `option_data.ntp_servers` | NetworkField |  |  |  |
| `option_data.time_servers` | NetworkField |  |  |  |
| `option_data.tftp_server_name` | TextField |  |  |  |
| `option_data.boot_file_name` | TextField |  |  |  |
| `option_data.v6_only_preferred` | IntegerField |  |  |  |
| `option_data.v4_dnr` | TextField |  |  |  |
| `option` | ModelRelationField, multiple |  |  |  |
| `match-client-id` | BooleanField | yes | `1` |  |
| `allocator` | OptionField |  |  | `iterative`, `random`, `flq` |
| `pools` | KeaPoolsField |  |  |  |
| `ping_check` | BooleanField | yes | `0` |  |
| `ddns_forward_zone` | HostnameField |  |  |  |
| `ddns_reverse_zone` | HostnameField |  |  |  |
| `ddns_qualifying_suffix` | HostnameField |  |  |  |
| `ddns_dns_server` | NetworkField |  |  |  |
| `ddns_dns_port` | PortField |  |  |  |
| `ddns_domain_key_name` | TextField |  |  |  |
| `ddns_domain_key_secret` (secret) | Base64Field |  |  |  |
| `ddns_domain_key_algorithm` | OptionField |  |  | `hmac-md5`, `hmac-sha1`, `hmac-sha224`, `hmac-sha256`, `hmac-sha384`, `hmac-sha512` |
| `ddns_override_no_update` | BooleanField |  |  |  |
| `ddns_override_client_update` | BooleanField |  |  |  |
| `ddns_update_on_renew` | BooleanField |  |  |  |
| `ddns_conflict_resolution_mode` | OptionField |  |  | `no-check-with-dhcid`, `check-exists-with-dhcid`, `no-check-without-dhcid` |
| `description` | DescriptionField |  |  |  |

### Examples

```yaml
- name: Add a subnet
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "subnet4"
    lookup: ["subnet"]
    actions:
      add: "addSubnet"
      del: "delSubnet"
      get: "getSubnet"
      search: "searchSubnet"
      set: "setSubnet"
    separators:
      pools: "\n"
    secret_fields: ["ddns_domain_key_secret"]
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "10.250.69.0/24"
          pools: ["10.250.69.100-10.250.69.199"]
          description: "routerops example"

- name: Remove a subnet
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "subnet4"
    lookup: ["subnet"]
    actions:
      add: "addSubnet"
      del: "delSubnet"
      get: "getSubnet"
      search: "searchSubnet"
      set: "setSubnet"
    separators:
      pools: "\n"
    secret_fields: ["ddns_domain_key_secret"]
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "10.250.69.0/24"
        state: "absent"
```
