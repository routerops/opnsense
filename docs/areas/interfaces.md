<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `interfaces`

## Assignment

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `interfaces/assignment` |
| Key | `interface` |
| Actions | default |
| Lookup | `descr` |
| Item ids | `name` |
| Apply | `interfaces/assignment/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-interfaces-assignnetworkports` ("Interfaces: Assign network ports", `api/interfaces/assignment/*`) |
| Minimum OPNsense | 26.7.6 |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Items are keyed by the interface name (`opt1`); the outcome `uuid` is that name, which a virtual IP takes as `interface`. The apply runs `interface apply` for every pending interface change, including ones made in the GUI, and can cut the management connection when it touches the interface you connect through. Set `lock: false`, or OPNsense refuses the delete. A deleted assignment takes its firewall and NAT rules with it and leaves its virtual IPs behind; delete those first. `type6: ""` means no IPv6. The examples assign the VLAN from the VLAN example, which must exist first.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Interfaces/NetworkInterface.xml#interface`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `descr` | IfDescField |  |  |  |
| `identifier` | TextField |  |  |  |
| `pending_action` | TextField |  |  |  |
| `icon` | TextField, not stored |  |  |  |
| `optgroup` | TextField, not stored |  |  |  |
| `if` | DeviceField | yes |  |  |
| `lock` | BooleanField | yes | `1` |  |
| `enable` | BooleanField | yes | `1` |  |
| `blockpriv` | BooleanField |  |  |  |
| `blockbogons` | BooleanField |  |  |  |
| `spoofmac` | MacAddressField |  |  |  |
| `promisc` | BooleanField |  |  |  |
| `media` | MediaTypesField |  |  |  |
| `hw_settings_overwrite` | BooleanField |  |  |  |
| `disablechecksumoffloading` | BooleanField |  |  |  |
| `disablesegmentationoffloading` | BooleanField |  |  |  |
| `disablelargereceiveoffloading` | BooleanField |  |  |  |
| `disablevlanhwfilter` | OptionField | yes | `0` | `0`, `1`, `2` |
| `gateway_interface` | BooleanField |  |  |  |
| `mtu` | IntegerField |  |  |  |
| `mss` | IntegerField |  |  |  |
| `type4` | OptionField |  |  | `staticv4`, `dhcp`, `pppoe`, `ppp`, `pptp`, `l2tp` |
| `type6` | OptionField |  |  | `staticv6`, `dhcp6`, `linklocal`, `slaac`, `6rd`, `6to4`, `idassoc6`, `track6`, `pppoev6` |
| `ipaddr` | NetworkField |  |  |  |
| `ipaddrv6` | NetworkField |  |  |  |
| `alias-address` | NetworkField |  |  |  |
| `alias-subnet` | IntegerField |  |  |  |
| `dhcprejectfrom` | NetworkField |  |  |  |
| `dhcphostname` | HostnameField |  |  |  |
| `dhcphonourmtu` | BooleanField |  |  |  |
| `dhcpvlanprio` | OptionField |  |  | `1`, `0`, `2`, `3`, `4`, `5`, `6`, `7` |
| `dhcp_send_options` | Dhcp4SendOptionsField |  |  |  |
| `dhcp_request_options` | Dhcp4RequestOptionsField |  |  |  |
| `dhcp6vlanprio` | OptionField |  |  | `1`, `0`, `2`, `3`, `4`, `5`, `6`, `7` |
| `dhcp6-ia-pd-len` | OptionField |  |  | `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11`, `12`, `13`, `14`, `15`, `16`, `none` |
| `dhcp6prefixonly` | BooleanField |  |  |  |
| `dhcp6_request_dns` | BooleanField |  |  |  |
| `dhcp6-information-only` | BooleanField |  |  |  |
| `dhcp6-ia-pd-send-hint` | BooleanField |  |  |  |
| `dhcp6_rapid_commit` | BooleanField |  |  |  |
| `dhcp6-prefix-id` | TextField |  |  |  |
| `dhcp6_ifid` | TextField |  |  |  |
| `dhcp6_assoc_pd` | IntegerField |  |  |  |
| `dhcp6_send_options` | Dhcp6SendOptionsField |  |  |  |
| `dhcp6_request_options` | Dhcp6RequestOptionsField |  |  |  |
| `prefix-6rd` | NetworkField |  |  |  |
| `gateway-6rd` | NetworkField |  |  |  |
| `prefix-6rd-v4plen` | IntegerField |  |  |  |
| `prefix-6rd-v4addr` | NetworkField |  |  |  |
| `track6-interface` | InterfaceField |  |  |  |
| `track6-prefix-id` | TextField |  |  |  |
| `track6_ifid` | TextField |  |  |  |
| `track6_prefix_range` | IntegerField |  |  |  |
| `track6_assoc_pd` | IntegerField |  |  |  |
| `dhcpd6track6allowoverride` | BooleanField |  |  |  |
| `gateway` | GatewayField |  |  |  |
| `gatewayv6` | GatewayField |  |  |  |

### Examples

```yaml
- name: Assign a VLAN with a static address
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/assignment"
    key: "interface"
    lookup: ["descr"]
    id_format: "name"
    apply: "interfaces/assignment/reconfigure"
    items:
      - fields:
          if: "vlan0.4009"
          descr: "rt_example"
          enable: true
          lock: false
          type4: "staticv4"
          ipaddr: "10.250.49.1/24"
          type6: ""

- name: Remove an assignment
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/assignment"
    key: "interface"
    lookup: ["descr"]
    id_format: "name"
    apply: "interfaces/assignment/reconfigure"
    items:
      - fields:
          descr: "rt_example"
        state: "absent"
```

## Virtual IP

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `interfaces/vip_settings` |
| Key | `vip` |
| Actions | default |
| Lookup | `descr` |
| Item ids | `uuid` |
| Apply | `interfaces/vip_settings/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `password` |
| Separators | - |
| Privileges | `page-firewall-virtualipaddress-edit` ("Interfaces: Virtual IPs: Settings", `api/interfaces/vip_settings/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Send the address as `network`; OPNsense reads and returns it in that form, not as `subnet` and `subnet_bits`. Descriptions identify a virtual IP; keep them unique. A CARP `password` is returned in clear, so name it in `secret_fields`.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Interfaces/Vip.xml#vip`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `interface` | VipInterfaceField | yes |  |  |
| `mode` | OptionField | yes | `ipalias` | `ipalias`, `carp`, `proxyarp` |
| `subnet` | VipNetworkField |  |  |  |
| `subnet_bits` | VipNetworkField |  |  |  |
| `gateway` | NetworkField |  |  |  |
| `noexpand` | BooleanField | yes | `0` |  |
| `nobind` | BooleanField | yes | `0` |  |
| `password` (secret) | TextField |  |  |  |
| `vhid` | IntegerField |  |  |  |
| `advbase` | IntegerField | yes | `1` |  |
| `advskew` | IntegerField | yes | `0` |  |
| `peer` | NetworkField |  |  |  |
| `peer6` | NetworkField |  |  |  |
| `nosync` | BooleanField | yes | `0` |  |
| `address` | TextField, not stored |  |  |  |
| `vhid_txt` | TextField, not stored |  |  |  |
| `descr` | DescriptionField |  |  |  |
| `network` | API only: address and prefix length (`10.250.1.240/24`), which OPNsense stores as `subnet` and `subnet_bits` | | | |

### Examples

```yaml
- name: Add an IP alias on LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vip_settings"
    key: "vip"
    lookup: ["descr"]
    secret_fields: ["password"]
    apply: "interfaces/vip_settings/reconfigure"
    items:
      - fields:
          mode: "ipalias"
          interface: "lan"
          network: "10.250.1.250/24"
          descr: "routerops example"

- name: Remove a virtual IP
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vip_settings"
    key: "vip"
    lookup: ["descr"]
    secret_fields: ["password"]
    apply: "interfaces/vip_settings/reconfigure"
    items:
      - fields:
          descr: "routerops example"
        state: "absent"
```

## VLAN

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `interfaces/vlan_settings` |
| Key | `vlan` |
| Actions | default |
| Lookup | `descr` |
| Item ids | `uuid` |
| Apply | `interfaces/vlan_settings/reconfigure` |
| Write-only fields | - |
| Ordered fields | - |
| Always sent | - |
| Secret fields | - |
| Separators | - |
| Privileges | `page-interfaces-vlan-edit` ("Interfaces: VLAN", `api/interfaces/vlan_settings/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

Set `vlanif` (`vlan0.<tag>`) so the device name is known before the VLAN is assigned; OPNsense refuses to delete a VLAN that is assigned as an interface.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/Interfaces/Vlan.xml#vlan`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `if` | VlanInterfaceField | yes |  |  |
| `tag` | IntegerField | yes |  |  |
| `pcp` | OptionField | yes | `0` | `1`, `0`, `2`, `3`, `4`, `5`, `6`, `7` |
| `proto` | OptionField |  |  | `802.1q`, `802.1ad` |
| `descr` | DescriptionField |  |  |  |
| `vlanif` | TextField | yes |  |  |

### Examples

```yaml
- name: Add a VLAN on the LAN port
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vlan_settings"
    key: "vlan"
    lookup: ["descr"]
    apply: "interfaces/vlan_settings/reconfigure"
    items:
      - fields:
          if: "vtnet1"
          tag: 4009
          vlanif: "vlan0.4009"
          descr: "routerops example"

- name: Remove a VLAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vlan_settings"
    key: "vlan"
    lookup: ["descr"]
    apply: "interfaces/vlan_settings/reconfigure"
    items:
      - fields:
          descr: "routerops example"
        state: "absent"
```
