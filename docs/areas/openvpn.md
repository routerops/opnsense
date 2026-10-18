<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `openvpn`

## OpenVPN instance

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `openvpn/instances` |
| Key | `instance` |
| Actions | `add: add`, `del: del`, `get: get`, `search: search`, `set: set` |
| Lookup | `description` |
| Item ids | `uuid` |
| Apply | `openvpn/service/reconfigure` |
| Write-only fields | `vpnid` |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `password` |
| Separators | - |
| Privileges | `page-openvpn-instances` ("VPN: OpenVPN: Instances", `api/openvpn/instances/*`), `page-status-openvpn` ("Status: OpenVPN", `api/openvpn/service/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.7 |
| Plugin | - |
| Stage | v0 |

`cert` and `ca` take a `refid` from the Trust areas; `tls_key` takes the uuid of a static key. OPNsense numbers instances itself, but only when `vpnid` arrives empty, so send `vpnid: ""` in `write_only`. The apply needs the privilege "Status: OpenVPN" and starts, restarts or stops every changed instance. Descriptions identify an instance; keep them unique. In the examples, replace `CERT_REFID` with the `refid` the example in the Certificate section returns.

### Fields

Read from `opnsense/core@26.7.7:src/opnsense/mvc/app/models/OPNsense/OpenVPN/OpenVPN.xml#Instances.Instance`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `vpnid` (write-only) | VPNIdField | yes |  |  |
| `enabled` | BooleanField | yes | `1` |  |
| `dev_type` | OptionField | yes | `tun` | `tun`, `tap`, `ovpn` |
| `verb` | OptionField | yes | `3` | `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`, `11` |
| `proto` | OptionField | yes | `udp` | `udp`, `udp4`, `udp6`, `tcp`, `tcp4`, `tcp6` |
| `port` | PortField |  |  |  |
| `port-share` | IPPortField |  |  |  |
| `local` | NetworkField |  |  |  |
| `topology` | OptionField | yes | `subnet` | `net30`, `p2p`, `subnet` |
| `remote` | RemoteHostField |  |  |  |
| `role` | OptionField | yes | `server` | `client`, `server` |
| `server` | NetworkField |  |  |  |
| `server_ipv6` | NetworkField |  |  |  |
| `nopool` | BooleanField |  |  |  |
| `bridge_gateway` | NetworkField |  |  |  |
| `bridge_pool` | TextField |  |  |  |
| `route` | NetworkField |  |  |  |
| `push_route` | NetworkField |  |  |  |
| `push_excluded_routes` | NetworkField |  |  |  |
| `cert` | CertificateField |  |  |  |
| `crl` | CertificateField |  |  |  |
| `ca` | CertificateField |  |  |  |
| `cert_depth` | OptionField |  |  | `1`, `2`, `3`, `4`, `5` |
| `remote_cert_tls` | BooleanField | yes | `0` |  |
| `verify_client_cert` | OptionField | yes | `require` | `none`, `require` |
| `use_ocsp` | BooleanField | yes | `0` |  |
| `auth` | OptionField |  |  | `BLAKE2b512`, `BLAKE2s256`, `MD4`, `MD5`, `MD5-SHA1`, `RIPEMD160`, `SHA1`, `SHA224`, `SHA256`, `SHA3-224`, `SHA3-256`, `SHA3-384`, `SHA3-512`, `SHA384`, `SHA512`, `SHA512-224`, `SHA512-256`, `SHAKE128`, `SHAKE256`, `whirlpool`, `none` |
| `data-ciphers` | OptionField, multiple |  |  | `AES-128-GCM`, `AES-192-GCM`, `AES-256-GCM`, `CHACHA20-POLY1305`, `AES-128-CBC`, `AES-192-CBC`, `AES-256-CBC`, `AES-128-CFB`, `AES-192-CFB`, `AES-256-CFB`, `AES-128-CFB1`, `AES-192-CFB1`, `AES-256-CFB1`, `AES-128-CFB8`, `AES-192-CFB8`, `AES-256-CFB8`, `AES-128-OFB`, `AES-192-OFB`, `AES-256-OFB` |
| `data-ciphers-fallback` | OptionField |  |  | `AES-128-GCM`, `AES-192-GCM`, `AES-256-GCM`, `CHACHA20-POLY1305`, `AES-128-CBC`, `AES-192-CBC`, `AES-256-CBC`, `AES-128-CFB`, `AES-192-CFB`, `AES-256-CFB`, `AES-128-CFB1`, `AES-192-CFB1`, `AES-256-CFB1`, `AES-128-CFB8`, `AES-192-CFB8`, `AES-256-CFB8`, `AES-128-OFB`, `AES-192-OFB`, `AES-256-OFB` |
| `tls_key` | ModelRelationField |  |  |  |
| `authmode` | AuthenticationServerField, multiple |  |  |  |
| `local_group` | AuthGroupField |  |  |  |
| `various_flags` | OptionField, multiple |  |  | `block-ipv6`, `client-to-client`, `duplicate-cn`, `float`, `passtos`, `persist-remote-ip`, `remote-random`, `route-noexec`, `route-nopull`, `explicit-exit-notify`, `fast-io` |
| `various_push_flags` | OptionField, multiple |  |  | `block-ipv6`, `block-outside-dns`, `register-dns`, `explicit-exit-notify` |
| `push_inactive` | IntegerField |  |  |  |
| `username_as_common_name` | BooleanField | yes | `0` |  |
| `strictusercn` | OptionField | yes | `0` | `0`, `1`, `2` |
| `username` | TextField |  |  |  |
| `password` (secret) | TextField |  |  |  |
| `maxclients` | IntegerField |  |  |  |
| `keepalive_interval` | IntegerField |  |  |  |
| `keepalive_timeout` | IntegerField |  |  |  |
| `reneg-sec` | IntegerField |  |  |  |
| `auth-gen-token` | IntegerField |  |  |  |
| `auth-gen-token-renewal` | IntegerField |  |  |  |
| `auth-gen-token-secret` | TextField |  |  |  |
| `provision_exclusive` | BooleanField | yes | `0` |  |
| `redirect_gateway` | OptionField, multiple |  |  | `local`, `autolocal`, `def1`, `bypass-dhcp`, `bypass-dns`, `block-local`, `ipv6`, `!ipv4` |
| `route_metric` | IntegerField |  |  |  |
| `register_dns` | BooleanField | yes | `0` |  |
| `dns_domain` | HostnameField |  |  |  |
| `dns_domain_search` | HostnameField |  |  |  |
| `dns_servers` | NetworkField |  |  |  |
| `ntp_servers` | NetworkField |  |  |  |
| `tun_mtu` | IntegerField |  |  |  |
| `fragment` | IntegerField |  |  |  |
| `mssfix` | BooleanField |  |  |  |
| `carp_depend_on` | VirtualIPField |  |  |  |
| `description` | DescriptionField |  |  |  |
| `compress_migrate` | BooleanField |  |  |  |
| `ifconfig-pool-persist` | BooleanField |  |  |  |
| `http-proxy` | IPPortField |  |  |  |
| `verify-x509-name` | StrictTextField |  |  |  |

### Examples

```yaml
- name: Run an OpenVPN server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "openvpn/instances"
    key: "instance"
    lookup: ["description"]
    actions:
      add: "add"
      del: "del"
      get: "get"
      search: "search"
      set: "set"
    secret_fields: ["password"]
    apply: "openvpn/service/reconfigure"
    items:
      - fields:
          role: "server"
          dev_type: "tun"
          proto: "udp"
          port: "11942"
          server: "10.250.82.0/24"
          cert: "CERT_REFID"
          description: "routerops example"
        write_only:
          vpnid: ""

- name: Remove an OpenVPN instance
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "openvpn/instances"
    key: "instance"
    lookup: ["description"]
    actions:
      add: "add"
      del: "del"
      get: "get"
      search: "search"
      set: "set"
    secret_fields: ["password"]
    apply: "openvpn/service/reconfigure"
    items:
      - fields:
          description: "routerops example"
        state: "absent"
```
