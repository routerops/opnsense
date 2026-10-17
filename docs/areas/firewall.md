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
