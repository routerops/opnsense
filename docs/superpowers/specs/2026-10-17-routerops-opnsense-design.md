# Design: `routerops.opnsense`, an Ansible collection for the OPNsense MVC API

Date: 2026-10-17. Builds on `docs/kickoff.md`, which stays the reference for the motivation, the OPNsense API facts and the Ansible style rules; this document records the decisions taken since and what v0 must deliver.

## Intent

`oxlorg.opnsense` ships one module per feature and lags behind OPNsense releases (no 26.7 release three months after 26.7, `nat_source` broken). Because the OPNsense MVC API is uniform, two generic modules can replace it: the caller names the endpoint and the fields, so a field change in a new OPNsense release is a change in the playbook, not in the collection.

The collection is public and meant for any user. v0 covers what operating an OPNsense firewall needs most, measured by evidence from OPNsense 26.7 and from the existing OPNsense automation projects, not by any single consumer's playbooks.

## Goals

- v0: every item type and settings singleton in the v0 scope below has a passing integration test against OPNsense 26.7 (add, update, idempotent rerun with `changed=0`, delete; settings: set, idempotent rerun, restore).
- No area-specific code in the collection; area differences are expressed through caller options (`actions`, `lookup`, `write_only`, apply path).
- Each new OPNsense RC is tested before its release, so a break shows up before consumers upgrade.

## Scope

Evidence: `opnsense/core` `stable/26.7` (126 API controllers) and the area coverage of `oxlorg.opnsense`, `browningluke/terraform-provider-opnsense`, `matthew-on-git/terraform-provider-opnsense` and `puzzle.opnsense` (the last one edits `config.xml` over SSH and counts only as a demand signal). Coverage = how many of the four projects manage the item type.

| Stage | Rule | Item types and settings |
|---|---|---|
| v0 | coverage 3 or more, testable on one VM; plus interface assignment: `AssignmentController` is new in 26.7 (absent in `stable/26.1`, added by opnsense/core#9945); from 26.7.6 on it is the only MVC way to set an interface's IP configuration (`NetworkInterface.xml` gains `enable`, `ipaddr`, `ipaddrv6`, `gateway`, `mtu` in tag 26.7.6, absent in 26.7 to 26.7.5), and a VLAN or VIP is unusable without it. The assignment tests and docs require 26.7.6 or later | Firewall: alias, filter rule, destination NAT, source NAT, one-to-one NAT. Interfaces: VLAN, virtual IP, assignment. Routes: static route. Auth: user. Unbound: general, host override, host alias, forward, ACL. Kea DHCPv4: general, subnet, reservation. Dnsmasq: host. WireGuard: server, peer. OpenVPN: instance, static key, client-specific override. IPsec: connection, local, remote, child, pre-shared key, VTI. Cron: job. Trust: CA and certificate as far as the OpenVPN tests need them. From the kickoff's feature bar, which it names as acceptance criteria (assistant's call to keep them in v0: one VM, no extra prerequisites): Routing: gateway. Dnsmasq: general, domain override, range, option. Syslog: destination |
| 0.x releases before v1 | coverage 2 | Trust: CA, certificate, settings. Auth: group. Firewall: category. Unbound: DNSBL. Kea: control agent, HA peer, DHCPv6. Dnsmasq: tag, boot. WireGuard: general. IPsec: pool, SPD, key pair. Monit. Traffic shaper. Interfaces: LAGG, bridge, GIF, GRE, loopback, VXLAN, neighbor. HA sync |
| v1 | coverage 0 or 1, or hard to test | Firewall: NPT, group. Routing: gateway group. Tunables. Auth: privileges. IDS. DHCP relay. Router advertisements. Captive portal. Kea DDNS. Boot environment snapshots. Trust: CRL |
| Plugins, tested | | v0: `os-acme-client`, `os-node_exporter`, `os-mdns-repeater`; after v0: `os-frr`, `os-haproxy`, `os-ddclient`, `os-bind`; every other plugin with an MVC API works untested (`docs/plugins.md`) |

Out of reach for `item` and `settings`, because 26.7 still configures them through legacy PHP pages without an MVC model: system general settings (hostname, DNS servers, time zone), the advanced system pages, authentication servers, NTP, PPPoE, firewall schedules and scrub. ISC DHCP is no longer in core.

Unverified in the coverage count: the `oxlorg.opnsense` modules `ipsec_cert`, `neighbor` and `dhcp_*` were mapped by name only. Whether LAGG, bridge or IDS tests need an extra NIC, more RAM or internet access was not tried; the first test run on the VM settles it.

## Non-goals (v0)

Firmware, packages, boot environment snapshots, filter rule savepoints or rollback (26.7 has no savepoint action), the legacy pages above, a Terraform provider, a GUI.

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
| Licence | the Ansible pattern from `collection_requirements.rst`: `plugins/modules/`, tests and everything else GPL-3.0-or-later; `plugins/module_utils/` BSD-2-Clause, so non-GPL projects can reuse the client and the normalisation (as ansible-core does with its own `module_utils`). Texts in `LICENSES/`, an SPDX header in every file (REUSE convention), checked by `reuse lint` in `make check`. Copyright lines read "routerops.opnsense contributors", no personal names. Contributions under the DCO, no CLA. No code is copied from `oxlorg.opnsense` (GPL-3.0), only ideas such as its test layout, so the BSD part stays clean. From `matthew-on-git/terraform-provider-opnsense` only facts are taken, never code or schema YAML text: its `LICENSE` says MIT with an unfilled owner placeholder while every `.go` file carries `SPDX-License-Identifier: MPL-2.0`; every fact taken from it is re-checked against `opnsense/core` or `opnsense/plugins` (BSD-2-Clause) |
| Supported OPNsense versions | the latest release only, plus each RC before its release; the previous release is best effort and untested; the README lists the tested versions |
| "Tested" means | `make integration` passes against that version |
| Integration target | a dedicated OPNsense VM in the owner's Proxmox, which the owner creates once (it does not exist yet) with `os-acme-client`, `os-node_exporter` and `os-mdns-repeater` installed; WAN and LAN on bridges without a physical port; the test host sits on the LAN bridge; the snapshot is rolled back before each run (`make integration` has no Proxmox access; `make integration-local` opens an SSH tunnel through the Proxmox host and reads the API credentials from Bitwarden, owner's decision on 17.10.2026); a new RC is tested on a clone that is upgraded |
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

- Success is `result == "saved"` for add and set, `result == "deleted"` for delete (`"not found"` counts as already gone), `status` equal to `ok` after trimming and ignoring case for `service/reconfigure`; never the HTTP code. A failed write fails the task and shows the `validations` map, a failed action shows `status_msg`. The firewall `apply` answers raw configd output as `status`; its exact success text is taken from a live 26.7 run before `item` accepts it (plan 2).
- A 404 or `Endpoint not found` fails with a message that names the path and says the area or plugin may be missing; integration tests skip an area whose catalog `plugin` is not installed.
- GET requests retry up to three times on a connection error or HTTP 5xx; POST requests never retry (assistant's call: a retried write can apply twice).
- Searches send `rowCount: -1`, which returns all rows (`UIModelGrid`), so there is no paging.
- Reads are normalised to the caller's plain form before comparing (option maps -> selected key or keys, `"0"`/`"1"` -> boolean, numbers -> string); the reference for the field types is the `matthew-on-git` generator table (`bool`, `int`, `string`, `selectmap`, `selectmaplist`). Edge cases the normalisation handles: a select read as `[]`, `null` or a plain string; an unset optional select read as `{"": {..., "selected": 1}}`; a string field returned as an option map (Dnsmasq host `ip`, `hwaddr`, `aliases`). Multi-select lists compare order-insensitive, except fields the caller names in `ordered_fields` (WireGuard peer `tunneladdress` keeps its order). Lists are joined with `,` except where the caller sets a separator per field in `separators` (alias `content` uses `\n`). Nested objects (destination NAT `source` and `destination` with `network`, `port`, `not`) are compared and written field by field (assistant's call for the option names).
- Only fields the caller names are compared and written.
- Check mode reads live and reports what would change without writing; it must not fail when the item does not exist yet.
- `--diff` shows before and after per field.
- `changed` only on a real write; one apply per call, skipped when nothing changed or when the caller passes no apply path.
- Return values include the identifier of every added or matched item.
- Fields OPNsense accepts but never returns (passwords, pre-shared keys, private keys, ACME DNS provider tokens) go with their values in a separate `write_only` option (a dict in the shape of `fields`, declared `no_log=True` so Ansible masks every value before it logs the arguments): they are left out of the compare and the diff, and are written only when an item is created, unless `update_write_only: always` (after Ansible's `update_password`) (assistant's call). A settings singleton is never created, so in `settings` the write-only values are only sent along with another change, and `update_write_only: always` is needed to set or rotate one.
- A reference to another item (an OpenVPN instance's certificate, an IPsec child's connection) is a UUID the caller takes from an earlier task's return value; the modules do not resolve references.
- The modules never reorder items; the caller sets `sequence` where order matters (filter rules, NAT).

Known traps go in the module docs and are not worked around: descriptions reject `-`; `destination_port` takes one port, range or alias; `type6` must be `none`, not `""`; a `set_item` the controller does not define answers `saved` and changes nothing (the caller overrides the action name); interface assignment items are keyed by the interface name (`setItem($ifname)`), not a UUID, and are looked up by their device field; its `reconfigure` runs `interface apply` and can cut the management connection.

## Repository and tooling

- Layout as in `docs/kickoff.md`, "First session in the new repo", step 2.
- `make check` is the one gate for humans, CI and agents: `ansible-lint` (production profile), `ansible-test sanity`, `ansible-test units` (pytest with mocked HTTP), gitleaks.
- `make integration` runs the integration tests against the test VM; it needs explicit opt-in and reads the URL and credentials from the environment, never from the repo.
- One integration test playbook per item type or settings singleton, plus a cleanup playbook (pattern from `oxlorg.opnsense` `tests/`). The interface assignment test touches only an extra VLAN interface, never WAN or LAN, so the test host keeps API access. VPN tests configure the tunnel without a peer; a tunnel coming up is not tested.
- `make plugin-inventory` rebuilds the generated part of `docs/plugins.md` from the `opnsense/plugins` tree with `gh api` and `jq`; a scheduled GitHub workflow runs it monthly and opens a pull request when a plugin is added, removed or gains an MVC API; the owner also runs it with each RC (assistant's call: monthly matches the plugin release pace, and the RC run catches a change before a release).
- `docs/testing.md` lists, for every tested area, the API privileges its test user needs, read from the area's `ACL.xml`.
- `AGENTS.md` is the standards document and carries the rules from `docs/kickoff.md`, "Ansible lessons" and "Working agreements to keep", including human review of every change; `CLAUDE.md` imports it with `@AGENTS.md` (owner's decision); skills live in `.agents/skills/` with `.claude/skills` as a symlink.
- Reference repositories under `.references/` (gitignored), listed in `reference-repos.md`, added with the `add-reference-repository` skill from the kickoff.
- Every dependency pinned to an exact version; Renovate bumps them.

## Area catalog and documentation

With generic modules, a user cannot guess an area's path, key or action names; the area documentation carries that knowledge, as the per-resource pages do in `matthew-on-git/terraform-provider-opnsense/docs/`.

| Part | Content |
|---|---|
| `meta/areas.yml` | one entry per tested item type or settings singleton: OPNsense area, `module` (`item` or `settings`), `path`, `key`, `actions`, default lookup, apply path, write-only field names, `ordered_fields`, `separators`, required API privileges, minimum OPNsense version where it is above the release (interface assignment: 26.7.6), OPNsense versions tested, plugin package if any, stage (v0, 0.x, v1) |
| `docs/areas/<area>.md` | generated from the catalog: one section per item type with the values above and one example task; generated, never edited by hand |
| README module and area table | generated from the catalog |
| `docs/migration-oxlorg.md` | which `oxlorg.opnsense` module maps to which `item` or `settings` call, with the matching catalog entry |
| `docs/limits.md` | what the modules cannot do: the legacy pages, no savepoints, the interface assignment risk and its 26.7.6 floor, ISC DHCP gone from core, integer fields where `0` is rejected and empty means unset (WireGuard `keepalive`, NAT `sequence` minimum 1), an empty NAT source stored as `""` and not `any`, and `throttle: 1` when several hosts write to one firewall (whether OPNsense locks its config during concurrent writes is unverified) |
| `make docs` | regenerates the generated files; `make check` fails when they differ from the committed ones |

Every integration test reads its path, key, actions and apply path from the catalog, so a tested catalog entry is a working documentation entry. A catalog entry, its integration test and its generated page land in the same change.

## Releases

| Topic | Decision |
|---|---|
| Versioning | SemVer; 0.x until v1; a breaking option change bumps the minor version while 0.x, the major version from 1.0 |
| Changelog | `antsibull-changelog` (0.35.1) fragments in `changelogs/fragments/`, one per user-visible change; `CHANGELOG.md` generated at release |
| Publishing | a GitHub workflow builds the collection and runs `ansible-galaxy collection publish` when a `v*` tag is pushed; the Galaxy API token lives in a repository secret; only the owner, or someone after the owner confirms, pushes a tag |
| Release check | before tagging: `make check` green, `make integration` green against the latest OPNsense release, `CHANGELOG.md` generated |

## Build order

1. Owner: create the test VM and its snapshot, the GitHub org and the Galaxy namespace. In parallel: scaffold the repository and add the reference repositories.
2. `settings` against `nodeexporter/general`.
3. `item` against `dnsmasq/settings` hosts (own action names `searchHost`, `addHost`, `setHost`, `delHost` in 26.7, so `actions` is proven first), then `firewall/alias` (default `*Item` names).
4. Prove it against a real consumer playbook: replace one `uri` block on a branch; `--check --diff` shows `changed=0`.
5. Area catalog, `make docs` and the first generated pages for the areas tested so far.
6. Work through the rest of the v0 scope and the three v0 plugins, each with catalog entry, test and page.
7. `docs/migration-oxlorg.md`, `docs/limits.md`, release workflow; tag `v0.1.0` after the owner confirms.
8. 0.x releases: the next stage of the scope, then the four plugins after v0.

## Privacy

The API key and secret never reach a log, a diff or the repo. DHCP reservations, Dnsmasq hosts, Unbound overrides and users can hold hostnames, MAC addresses and names, which can be personal data: test fixtures use invented values, and the module docs note that `--diff` prints these fields.

## Left to the builder

- The exact option names beyond those named here, and the exact return structure.
- How normalisation decides a field's type without a schema (from the read value's shape, from an optional caller hint, or both).
- The exact catalog schema beyond the fields listed in "Area catalog and documentation", and the generator's implementation (`jq`/`yq` and templates preferred over ad-hoc scripts).
- How the test VM gets a fresh API key after each snapshot rollback (for example a script over SSH, after the `browningluke` pattern of creating the key at runtime), or a key baked into the snapshot and read from the environment.
- Environment-variable fallbacks for the connection options.
