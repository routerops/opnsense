<!-- Generated from meta/areas.yml by make docs; do not edit. -->
# Area `trust`

## Certificate authority

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `trust/ca` |
| Key | `ca` |
| Actions | `add: add`, `del: del`, `get: get`, `search: search`, `set: set` |
| Lookup | `descr` |
| Item ids | `uuid` |
| Apply | - |
| Write-only fields | `action`, `key_type`, `digest`, `lifetime`, `commonname`, `country`, `city`, `state`, `organization`, `organizationalunit`, `email` |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `prv`, `prv_payload` |
| Separators | - |
| Privileges | `page-system-camanager` ("System: Trust: Authorities", `api/trust/ca/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.9 |
| Plugin | - |
| Stage | v0 |

The fields that create the CA (`action`, `commonname`, the key and lifetime settings) are not stored, so they go in `write_only` and are sent only when the CA is added. OPNsense applies a CA as soon as it is saved; there is nothing to apply. Read the `refid` that certificates and OpenVPN instances refer to with `return_fields: [refid]`. OPNsense deletes a CA even while certificates or instances use it. The private key is readable through the API; it is masked in the diff and the return values, and an imported key (`prv_payload`) belongs in `write_only`. Descriptions identify a CA; keep them unique.

### Fields

Read from `opnsense/core@26.7.9:src/opnsense/mvc/app/models/OPNsense/Trust/Ca.xml#ca`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `refid` | TextField |  |  |  |
| `descr` | DescriptionField | yes |  |  |
| `crt` | TextField |  |  |  |
| `prv` (secret) | TextField |  |  |  |
| `serial` | IntegerField |  |  |  |
| `caref` | CertificateField |  |  |  |
| `action` (write-only) | OptionField, not stored | yes | `internal` | `existing`, `internal`, `ocsp` |
| `key_type` (write-only) | OptionField, not stored | yes | `2048` | `512`, `1024`, `2048`, `3072`, `4096`, `7680`, `8192`, `prime256v1`, `secp384r1`, `secp521r1` |
| `digest` (write-only) | OptionField, not stored | yes | `sha256` | `sha1`, `sha224`, `sha256`, `sha384`, `sha512` |
| `lifetime` (write-only) | IntegerField, not stored | yes | `825` |  |
| `city` (write-only) | TextField, not stored |  |  |  |
| `state` (write-only) | TextField, not stored |  |  |  |
| `organization` (write-only) | TextField, not stored |  |  |  |
| `organizationalunit` (write-only) | TextField, not stored |  |  |  |
| `country` (write-only) | CountryField, not stored | yes | `NL` |  |
| `email` (write-only) | TextField, not stored |  |  |  |
| `commonname` (write-only) | TextField, not stored |  |  |  |
| `ocsp_uri` | UrlField, not stored |  |  |  |
| `crt_payload` | TextField, not stored |  |  |  |
| `prv_payload` (secret) | TextField, not stored |  |  |  |
| `refcount` | IntegerField, not stored |  |  |  |
| `name` | TextField, not stored |  |  |  |
| `valid_from` | TextField, not stored |  |  |  |
| `valid_to` | TextField, not stored |  |  |  |

### Examples

```yaml
- name: Create an internal CA
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "trust/ca"
    key: "ca"
    lookup: ["descr"]
    actions:
      add: "add"
      del: "del"
      get: "get"
      search: "search"
      set: "set"
    secret_fields: ["prv", "prv_payload"]
    return_fields: ["refid"]
    items:
      - fields:
          descr: "routerops example ca"
        write_only:
          action: "internal"
          commonname: "routerops-example-ca"
          country: "AT"

- name: Remove a CA
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "trust/ca"
    key: "ca"
    lookup: ["descr"]
    actions:
      add: "add"
      del: "del"
      get: "get"
      search: "search"
      set: "set"
    secret_fields: ["prv", "prv_payload"]
    items:
      - fields:
          descr: "routerops example ca"
        state: "absent"
```

## Certificate

| Setting | Value |
|---|---|
| Module | `routerops.opnsense.item` |
| Path | `trust/cert` |
| Key | `cert` |
| Actions | `add: add`, `del: del`, `get: get`, `search: search`, `set: set` |
| Lookup | `descr` |
| Item ids | `uuid` |
| Apply | - |
| Write-only fields | `action`, `key_type`, `digest`, `lifetime`, `cert_type`, `private_key_location`, `commonname`, `country`, `city`, `state`, `organization`, `organizationalunit`, `email`, `altnames_dns`, `altnames_ip`, `altnames_uri`, `altnames_email` |
| Ordered fields | - |
| Always sent | - |
| Secret fields | `prv`, `prv_payload` |
| Separators | - |
| Privileges | `page-system-certmanager` ("System: Trust: Certificates", `api/trust/cert/*`) |
| Minimum OPNsense | - |
| Tested on | 26.7.9 |
| Plugin | - |
| Stage | v0 |

`caref` is the `refid` of the signing CA. The fields that create the certificate (`action`, `cert_type`, `commonname`, the key, lifetime and alternative names) are not stored, so they go in `write_only` and are sent only when the certificate is added. Separate several `altnames_dns` with a newline. Every update reissues the certificate with the same key. A certificate an OpenVPN instance uses cannot be deleted; OPNsense answers HTTP 500 "Item in use by". The private key is readable through the API; it is masked in the diff and the return values, and an imported key (`prv_payload`) belongs in `write_only`. Do not use `private_key_location: local`: OPNsense then returns the new key only once, in the answer to the add, and the module does not return it, so the key is lost. Descriptions identify a certificate; keep them unique. In the examples, replace `CA_REFID` with the `refid` the example in the Certificate authority section returns.

### Fields

Read from `opnsense/core@26.7.9:src/opnsense/mvc/app/models/OPNsense/Trust/Cert.xml#cert`.

| Field | Type | Required | Default | Values |
|---|---|---|---|---|
| `refid` | TextField |  |  |  |
| `descr` | DescriptionField | yes |  |  |
| `caref` | CertificateField |  |  |  |
| `crt` | TextField |  |  |  |
| `csr` | TextField |  |  |  |
| `prv` (secret) | TextField |  |  |  |
| `action` (write-only) | OptionField, not stored | yes | `internal` | `internal`, `external`, `import`, `sign_csr`, `import_csr`, `reissue`, `manual` |
| `key_type` (write-only) | OptionField, not stored | yes | `2048` | `512`, `1024`, `2048`, `3072`, `4096`, `7680`, `8192`, `prime256v1`, `secp384r1`, `secp521r1` |
| `digest` (write-only) | OptionField, not stored | yes | `sha256` | `sha1`, `sha224`, `sha256`, `sha384`, `sha512` |
| `cert_type` (write-only) | OptionField, not stored | yes | `usr_cert` | `usr_cert`, `server_cert`, `combined_server_client`, `v3_ca` |
| `lifetime` (write-only) | IntegerField, not stored | yes | `397` |  |
| `private_key_location` (write-only) | OptionField, not stored | yes | `firewall` | `firewall`, `local` |
| `city` (write-only) | TextField, not stored |  |  |  |
| `state` (write-only) | TextField, not stored |  |  |  |
| `organization` (write-only) | TextField, not stored |  |  |  |
| `organizationalunit` (write-only) | TextField, not stored |  |  |  |
| `country` (write-only) | CountryField, not stored | yes | `NL` |  |
| `email` (write-only) | TextField, not stored |  |  |  |
| `commonname` (write-only) | TextField, not stored |  |  |  |
| `ocsp_uri` | UrlField, not stored |  |  |  |
| `altnames_dns` (write-only) | TextField, not stored |  |  |  |
| `altnames_ip` (write-only) | TextField, not stored |  |  |  |
| `altnames_uri` (write-only) | TextField, not stored |  |  |  |
| `altnames_email` (write-only) | TextField, not stored |  |  |  |
| `crt_payload` | TextField, not stored |  |  |  |
| `csr_payload` | TextField, not stored |  |  |  |
| `prv_payload` (secret) | TextField, not stored |  |  |  |
| `rfc3280_purpose` | TextField, not stored |  |  |  |
| `in_use` | BooleanField, not stored |  |  |  |
| `is_user` | BooleanField, not stored |  |  |  |
| `name` | TextField, not stored |  |  |  |
| `valid_from` | TextField, not stored |  |  |  |
| `valid_to` | TextField, not stored |  |  |  |

### Examples

```yaml
- name: Create a server certificate
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "trust/cert"
    key: "cert"
    lookup: ["descr"]
    actions:
      add: "add"
      del: "del"
      get: "get"
      search: "search"
      set: "set"
    secret_fields: ["prv", "prv_payload"]
    return_fields: ["refid"]
    items:
      - fields:
          descr: "routerops example server"
          caref: "CA_REFID"
        write_only:
          action: "internal"
          cert_type: "server_cert"
          commonname: "rt-example-server"

- name: Remove a certificate
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "trust/cert"
    key: "cert"
    lookup: ["descr"]
    actions:
      add: "add"
      del: "del"
      get: "get"
      search: "search"
      set: "set"
    secret_fields: ["prv", "prv_payload"]
    items:
      - fields:
          descr: "routerops example server"
        state: "absent"
```
