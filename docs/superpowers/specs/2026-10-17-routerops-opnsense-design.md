# Design: `routerops.opnsense`, an Ansible collection for the OPNsense MVC API

Date: 2026-10-17. Builds on `docs/kickoff.md`, which stays the reference for the motivation, the OPNsense API facts and the Ansible style rules; this document records the decisions taken since and what v0 must deliver.

## Intent

`oxlorg.opnsense` ships one module per feature and lags behind OPNsense releases (no 26.7 release three months after 26.7, `nat_source` broken). Because the OPNsense MVC API is uniform, two generic modules can replace it: the caller names the endpoint and the fields, so a field change in a new OPNsense release is a change in the playbook, not in the collection.

The collection is public and meant for any user. v0 covers what operating an OPNsense firewall needs most, measured by evidence from OPNsense 26.7 and from the existing OPNsense automation projects, not by any single consumer's playbooks.

## Goals

- v0: every item type and settings singleton in the v0 scope below has a passing integration test against OPNsense 26.7 (add, update, idempotent rerun with `changed=0`, delete; settings: set, idempotent rerun, restore).
- No area-specific code in the collection; area differences are expressed through caller options (`actions`, `lookup`, `write_only_fields`, apply path).
- Each new OPNsense RC is tested before its release, so a break shows up before consumers upgrade.

## Scope

Evidence: `opnsense/core` `stable/26.7` (126 API controllers) and the area coverage of `oxlorg.opnsense`, `browningluke/terraform-provider-opnsense`, `matthew-on-git/terraform-provider-opnsense` and `puzzle.opnsense` (the last one edits `config.xml` over SSH and counts only as a demand signal). Coverage = how many of the four projects manage the item type.

| Stage | Rule | Item types and settings |
|---|---|---|
| v0 | coverage 3 or more, testable on one VM; plus interface assignment: new in 26.7 (`AssignmentController` is absent in `stable/26.1`, added by opnsense/core#9945), the only MVC way to set an interface's IP configuration (`NetworkInterface.xml`: `enable`, `ipaddr`, `ipaddrv6`, `gateway`, `mtu`), and needed before a VLAN or VIP is usable | Firewall: alias, filter rule, destination NAT, source NAT, one-to-one NAT. Interfaces: VLAN, virtual IP, assignment. Routes: static route. Auth: user. Unbound: general, host override, host alias, forward, ACL. Kea DHCPv4: general, subnet, reservation. Dnsmasq: host. WireGuard: server, peer. OpenVPN: instance, static key, client-specific override. IPsec: connection, local, remote, child, pre-shared key, VTI. Cron: job. Trust: CA and certificate as far as the OpenVPN tests need them |
| 0.x releases before v1 | coverage 2 | Trust: CA, certificate, settings. Routing: gateway. Auth: group. Firewall: category. Unbound: DNSBL. Kea: control agent, HA peer, DHCPv6. Dnsmasq: domain override, range, option, tag, boot, general. WireGuard: general. IPsec: pool, SPD, key pair. Syslog destination. Monit. Traffic shaper. Interfaces: LAGG, bridge, GIF, GRE, loopback, VXLAN, neighbor. HA sync |
| v1 | coverage 0 or 1, or hard to test | Firewall: NPT, group. Routing: gateway group. Tunables. Auth: privileges. IDS. DHCP relay. Router advertisements. Captive portal. Kea DDNS. Boot environment snapshots. Trust: CRL |
| Plugins, tested | | v0: `os-acme-client`, `os-node_exporter`, `os-mdns-repeater`; after v0: `os-frr`, `os-haproxy`, `os-ddclient`, `os-bind`; every other plugin with an MVC API works untested (`docs/plugins.md`) |

Out of reach for `item` and `settings`, because 26.7 still configures them through legacy PHP pages without an MVC model: system general settings (hostname, DNS servers, time zone), the advanced system pages, authentication servers, NTP, PPPoE, firewall schedules and scrub. ISC DHCP is no longer in core.

Unverified in the coverage count: the `oxlorg.opnsense` modules `ipsec_cert`, `neighbor` and `dhcp_*` were mapped by name only. Whether LAGG, bridge or IDS tests need an extra NIC, more RAM or internet access was not tried; the first test run on the VM settles it.

## Non-goals (v0)

Firmware, packages, boot environment snapshots, filter rule savepoints or rollback (26.7 has no savepoint action), the legacy pages above, a Terraform provider, a GUI, a per-area schema catalog shipped as a requirement (see "Left to the builder").

## Anti-goals

- An integration test that can reach a production router.
- A module that reports `changed` without a real write, or writes in check mode.
- The API key or secret in any log, diff or test fixture.
- One module per OPNsense area.

## Decisions

| Topic | Decision |
|---|---|
| Hosting | public GitHub org `routerops`; the owner creates the org and the Galaxy namespace by hand |
| Collection | `routerops.opnsense`, released on Galaxy; publishing and pushing tags only after the owner confirms |
| Licence | GPL-3.0-or-later; code and test patterns from `oxlorg.opnsense` may be reused with attribution |
| Supported OPNsense versions | the latest release only, plus each RC before its release; the previous release is best effort and untested; the README lists the tested versions |
| "Tested" means | `make integration` passes against that version |
| Integration target | a dedicated OPNsense VM in the owner's Proxmox, which the owner creates once (it does not exist yet) with `os-acme-client`, `os-node_exporter` and `os-mdns-repeater` installed; WAN and LAN on bridges without a physical port; the test host sits on the LAN bridge; the owner rolls back a snapshot by hand before each run (`make integration` has no Proxmox access); a new RC is tested on a clone that is upgraded |
| Where tests run | integration tests run locally and by hand (`make integration`, opt-in); CI (GitHub-hosted) runs only `ansible-test sanity`, `ansible-test units` and lint; no self-hosted runner, because fork PRs would run code inside the owner's network |
| Module names | `routerops.opnsense.item` and `routerops.opnsense.settings` (assistant's call: the collection name already says "opnsense") |
| Plugin inventory | `docs/plugins.md` lists every plugin in `opnsense/plugins` with or without an MVC API; a scheduled check keeps it current (see "Repository and tooling") |

## The two modules

Shared connection options (`url`, `api_key`, `api_secret`, `validate_certs` default `true`), all usable through `module_defaults` with an action group in `meta/runtime.yml` (assistant's call). `api_secret` and `api_key` carry `no_log`.

| | `settings` | `item` |
|---|---|---|
| Purpose | settings singleton: `get`, compare, `set` only the differing fields; works on every model controller, because `ApiMutableModelControllerBase` provides `get` and `set` | items: search, then add, set or delete |
| Caller passes | controller base path (`unbound/settings`), the JSON wrapper key, the wanted fields, the apply path | controller base path (`firewall/alias`), the item key (`alias`), a list of wanted items, the lookup: one field (default `description`) or a list of fields forming a composite key, the apply path |
| Action names | `get`, `set` by default; overridable through `actions` | `search_item`, `get_item`, `add_item`, `set_item`, `del_item` by default; overridable through an `actions` dict, required for most areas: 26.7 core uses `*Item` (alias, VLAN, VIP), `*Rule` (filter, NAT), bare `search`/`add` (user, CA, certificate, OpenVPN), lowercase `searchroute`/`addroute` (routes) and own stems (`*Gateway`, `*Job`, `*HostOverride`, `*Subnet`) |
| Apply | the apply path is a caller option: `service/reconfigure` for most areas, `apply` for firewall rules and NAT, none to skip | same |
| Delete | n/a | an item with `state: absent`; `purge: true` deletes every item of that key the caller did not list |

`item` takes a list of items in one call (assistant's call: `purge` only makes sense over a list, and one call means one apply). Lookup values must be unique among the listed items; a lookup value that matches more than one existing item fails the task instead of guessing.

Both modules:

- Success is `result == "saved"` (or `status == "ok"` for an action), never the HTTP code; a failed write fails the task and shows the `validations` map.
- Reads are normalised to the caller's plain form before comparing (option maps -> selected key or keys, `"0"`/`"1"` -> boolean, numbers -> string); the reference for the field types is the `matthew-on-git` generator table (`bool`, `int`, `string`, `selectmap`, `selectmaplist`).
- Only fields the caller names are compared and written.
- Check mode reads live and reports what would change without writing; it must not fail when the item does not exist yet.
- `--diff` shows before and after per field.
- `changed` only on a real write; one apply per call, skipped when nothing changed or when the caller passes no apply path.
- Return values include the identifier of every added or matched item.
- Fields OPNsense accepts but never returns (passwords, pre-shared keys, private keys, ACME DNS provider tokens) go in `write_only_fields`: they are left out of the compare and the diff, carry `no_log`, and are written only when an item is created, unless `update_write_only: always` (after Ansible's `update_password`) (assistant's call).
- A reference to another item (an OpenVPN instance's certificate, an IPsec child's connection) is a UUID the caller takes from an earlier task's return value; the modules do not resolve references.
- The modules never reorder items; the caller sets `sequence` where order matters (filter rules, NAT).

Known traps go in the module docs and are not worked around: descriptions reject `-`; `destination_port` takes one port, range or alias; `type6` must be `none`, not `""`; a `set_item` the controller does not define answers `saved` and changes nothing (the caller overrides the action name); interface assignment items are keyed by the interface name (`setItem($ifname)`), not a UUID, and are looked up by their device field; its `reconfigure` runs `interface apply` and can cut the management connection.

## Repository and tooling

- Layout as in `docs/kickoff.md`, "First session in the new repo", step 2.
- `make check` is the one gate for humans, CI and agents: `ansible-lint` (production profile), `ansible-test sanity`, `ansible-test units` (pytest with mocked HTTP), gitleaks.
- `make integration` runs the integration tests against the test VM; it needs explicit opt-in and reads the URL and credentials from the environment, never from the repo.
- One integration test playbook per item type or settings singleton, plus a cleanup playbook (pattern from `oxlorg.opnsense` `tests/`). The interface assignment test touches only an extra VLAN interface, never WAN or LAN, so the test host keeps API access. VPN tests configure the tunnel without a peer; a tunnel coming up is not tested.
- `make plugin-inventory` rebuilds the generated part of `docs/plugins.md` from the `opnsense/plugins` tree with `gh api` and `jq`; a scheduled GitHub workflow runs it monthly and opens a pull request when a plugin is added, removed or gains an MVC API; the owner also runs it with each RC (assistant's call: monthly matches the plugin release pace, and the RC run catches a change before a release).
- `CLAUDE.md` is the standards document; `AGENTS.md` points to it; skills live in `.agents/skills/` with `.claude/skills` as a symlink.
- Reference repositories under `.references/` (gitignored), listed in `reference-repos.md`, added with the `add-reference-repository` skill from the kickoff.
- Every dependency pinned to an exact version; Renovate bumps them.

## Build order

1. Owner: create the test VM and its snapshot, the GitHub org and the Galaxy namespace. In parallel: scaffold the repository and add the reference repositories.
2. `settings` against `nodeexporter/general`.
3. `item` against `firewall/alias`, then a type with different action names (`routes/routes`) to prove `actions`.
4. Prove it against a real consumer playbook: replace one `uri` block on a branch; `--check --diff` shows `changed=0`.
5. Work through the rest of the v0 scope and the three v0 plugins.
6. 0.x releases: the next stage of the scope, then the four plugins after v0.

## Privacy

The API key and secret never reach a log, a diff or the repo. DHCP reservations, Dnsmasq hosts, Unbound overrides and users can hold hostnames, MAC addresses and names, which can be personal data: test fixtures use invented values, and the module docs note that `--diff` prints these fields.

## Left to the builder

- The exact option names beyond those named here, and the exact return structure.
- How normalisation decides a field's type without a schema (from the read value's shape, from an optional caller hint, or both).
- Whether a per-area YAML catalog (endpoints, item key, action names, field types) lives in `meta/` for tests and docs; not required for v0.
- How the test VM gets a fresh API key after each snapshot rollback (for example a script over SSH, after the `browningluke` pattern of creating the key at runtime), or a key baked into the snapshot and read from the environment.
- Environment-variable fallbacks for the connection options.
