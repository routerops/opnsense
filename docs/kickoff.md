# Kickoff: an Ansible collection for the OPNsense MVC API

Date: 2026-10-17. Starting point for this repository; a new Claude Code session can begin from it alone.

## Why

The first consumer manages an OPNsense router with `oxlorg.opnsense` plus raw `ansible.builtin.uri` calls. `oxlorg.opnsense` ships one module per feature, and its README says each release fits one OPNsense version only. It had no release for 26.7 three months after 26.7 shipped, `nat_source` broke on 26.7, and the modules the consumer uses most (`nat_destination`, `dnsmasq_*`) are marked unstable. Alternatives checked on 17.10.2026: `matthew-on-git/opnsense` (Terraform, one author, pre-1.0, no interface assignment, node_exporter, mdns-repeater or packages), `browningluke/opnsense` (Terraform, no ACME, syslog, gateway or full Dnsmasq), `puzzle.opnsense` (edits config.xml over SSH, no DNS, DHCP or NAT); none replaces it.

The OPNsense MVC API is uniform: almost every area offers `search_item`, `get_item`, `add_item`, `set_item`, `del_item` (or `get`/`set` for a settings singleton), then `service/reconfigure`. The field definitions live in the model XML files of `opnsense/core` (`src/opnsense/mvc/app/models/OPNsense/<Area>/*.xml`) and of `opnsense/plugins`. So a small set of generic modules can cover what `oxlorg.opnsense` covers with dozens, and a field change in a new OPNsense release becomes a data change in the caller's playbook instead of a code change in the collection.

`matthew-on-git/terraform-provider-opnsense` reached the same split independently: its generator (`internal/generate/`) knows two resource kinds, `item` (UUID CRUD) and `singleton` (get/set), each with endpoints, a JSON wrapper key and a `reconfigure` path.

## Goal and scope

| | |
|---|---|
| v0 goal | the consumer's five OPNsense playbooks can drop every `oxlorg.opnsense` module and every hand-written `uri` read-compare-write block |
| Modules | `opnsense_item`: find an item by a lookup field (default `description`), add, update or delete it, optional `purge` of items the caller did not list. `opnsense_settings`: read a settings singleton, set only the differing fields. Both take the controller base path (`dnsmasq/settings`), the item key (`host`), the wanted fields and the `reconfigure` path |
| Shared code | `plugins/module_utils/` for the HTTP client (API key and secret, TLS verify on by default), the error mapping and the normalisation below |
| Behaviour | idempotent; check mode reads live and reports without writing; `--diff` shows per-field before and after; `changed` only on a real write; one `reconfigure` per module call, skipped when nothing changed |
| Not in v0 | firmware, packages, interface assignment, filter rules with savepoints, a Terraform provider, a GUI |

### Initial feature bar (acceptance criteria)

| Area | Endpoints today | Kind |
|---|---|---|
| Aliases, filter rules | `firewall/alias`, `firewall/filter` (with purge) | item |
| Destination NAT | `firewall/d_nat` | item |
| Dnsmasq | `dnsmasq/settings` general, domain overrides, hosts, options, ranges | settings singleton + items |
| Kea DHCP, Unbound | general settings (both switched off) | settings singleton |
| VLAN devices | `interfaces/vlan_settings` | item |
| ACME | `acmeclient/certificates`, `acmeclient/validations` (update through the controller's own action) | item |
| Syslog | `syslog/settings` destinations | item |
| Gateway monitor | `routing/settings` gateways | item |
| node_exporter, mdns-repeater | `nodeexporter/general`, `mdnsrepeater/settings` | settings singleton |

## OPNsense API facts to build on

| Fact | Consequence for the modules |
|---|---|
| A rejected write answers HTTP 200 with `{"result":"failed","validations":{...}}` | success is `result == "saved"` (or `status == "ok"` for actions), never the HTTP code; surface `validations` in the error |
| A `set/<uuid>` that the area's controller does not define falls through to the base class, answers `saved` and changes nothing | per area, check the controller in `opnsense/core` or `opnsense/plugins` for its own action names (`acmeclient/validations/update/<uuid>`, `interfaces/assignment/set_item/<id>`) and let the caller override the action path |
| Reads return option fields as maps (`{"value": {"value": "...", "selected": 1}}`), booleans as `"0"`/`"1"`, numbers as strings | normalise a read to the caller's plain form before comparing: the selected key(s), `true`/`false`, the string; the `matthew-on-git` generator's field-type table (`bool`, `int`, `string`, `selectmap`, `selectmaplist`) is the reference |
| Descriptions reject `-`; `destination_port` takes one port, range or alias; interface `type6` must be `none`, not `""` | validation errors, not module bugs; document them in the module docs |
| Filter rule savepoints (`firewall/filter/savepoint`, `apply/<rev>`, `cancelRollback`) answer 404 on 26.7 | no automatic rollback for filter rules; out of v0 |
| Granting an API user privileges is a GUI or admin step | the test setup documents which privileges each module needs |
| OPNsense supports only its latest release; two releases a year (January, July), RCs about a week before | the collection names the OPNsense versions it is tested on and runs its tests against each new RC |

## Ansible lessons

Style: Tier A (docs.ansible.com) plus Tier B (Red Hat CoP Automation Good Practices) for every new line. The points that matter most for a collection:

| Rule | Why |
|---|---|
| FQCN everywhere; every task named in the imperative; `ansible-lint` production profile | the profile catches most of it before review |
| Inputs with a role or module prefix, internals `__<prefix>_`; bracket notation for key access (`x['stdout']`) | avoids name clashes and the dot-notation pitfalls on dict methods |
| Every role has `meta/argument_specs.yml`; every module has full `DOCUMENTATION`, `EXAMPLES`, `RETURN` | `ansible-doc` and `ansible-test sanity` read them; the README table is generated, not hand-written |
| `no_log: true` on secret inputs; `diff: false` where a secret would land in a diff | the API key and secret must never reach a log or a diff |
| Check mode must not fail on a fresh target, and a rerun shows `changed=0` | consumers gate every live change on `--check --diff` and an idempotency rerun |
| `\| int` or `\| bool` before comparing a templated value; health checks match an expected answer, never `grep -q .` | Jinja renders strings; `dig +short` prints errors to stdout |
| Pin every dependency to an exact version; Renovate bumps it | an unpinned dependency changes behaviour without a commit |
| A new check or assert counts as verified only after it failed once against a real fault | a check never seen failing proves nothing |

For a collection on top: `ansible-test sanity` and `ansible-test units` (pytest with a mocked HTTP layer) in CI; integration tests against a real OPNsense behind an opt-in flag, like the provider's `TF_ACC=1` acceptance job (`.github/workflows/acceptance.yml`, credentials from repo secrets, run by hand).

Comments: zero by default; one only for a "why" the code cannot show, at most one line; never one that restates the code or that you have not checked. Docs: one fact in one place, tables over long lists, no hard-wrapped prose.

## AI setup, after `matthew-on-git/terraform-provider-opnsense`

What that repo does, and what to take:

| There | Take it? |
|---|---|
| One canonical standards document (`DEVELOPMENT.md`); `AGENTS.md`, `CLAUDE.md` and `.cursorrules` are thin pointers that repeat only the critical rules | yes: `CLAUDE.md` as the source, `AGENTS.md` pointing to it for other agents |
| One gate command for humans, CI and agents (`make check`: lint, format, tests, security, docs) | yes: `make check` running `ansible-lint`, `ansible-test sanity`, `ansible-test units`, gitleaks |
| A generator from declarative YAML schemas instead of hand-written near-identical files | yes in spirit: the generic modules take the schema as input; a per-area YAML catalog (endpoints, item key, field types) can live in `meta/` and feed tests and docs |
| Acceptance tests against a live OPNsense, opt-in, secrets from CI | yes; needs a test OPNsense (open question below) |
| Shared skill tree `.agents/skills/` read by several agents | yes, with `.claude/skills` as a symlink to it so Claude Code finds the same skills |
| BMAD method and `bmad-loop` orchestration (`_bmad/`, `.opencode/`, `_bmad-output/`), a dev toolchain container | no: heavy, and it produced mostly agent-written code with one maintainer; this project uses the superpowers flow (brainstorm, spec, plan) and human review of every change |

Working agreements to keep: English for code, comments, commits and docs; chat in the owner's language; commit at logical checkpoints; confirm before destructive or outward-facing actions (publishing to Galaxy, pushing tags).

## Reference repositories

Keep read-only clones under `.references/` (gitignored) with the skill below, and list them in `reference-repos.md`:

| Name | URL | Why |
|---|---|---|
| `opnsense-core` | https://github.com/opnsense/core | model XML and controllers: field names, action names, validation |
| `opnsense-plugins` | https://github.com/opnsense/plugins | same for ACME, node_exporter, mdns-repeater |
| `ansible-opnsense` | https://github.com/O-X-L/ansible-opnsense | how `oxlorg.opnsense` maps each area; known breakages |
| `terraform-provider-opnsense` | https://github.com/matthew-on-git/terraform-provider-opnsense | the item/singleton schema catalog and field-type conversions |

Put this skill at `.agents/skills/add-reference-repository/SKILL.md` (source: an earlier project of the owner):

```markdown
---
name: add-reference-repository
description: Clones a reference repository into `.references/<name>` and prepares it for reuse. Use when adding, refreshing, or bootstrapping a local reference repo from GitHub or another git remote.
---

# Add Reference Repository

## Quick Start

Create or reuse the current repo's `.references/` directory, then clone the requested repository into `.references/<name>`.

If the target path already exists, do not overwrite it blindly. Inspect the existing repo first and only replace it if the user explicitly asks.

## Workflow

1. Resolve the target name and clone URL.
2. Ensure `.references/` exists at the root of the current repository.
3. Clone the remote into `.references/<name>`.
4. If the cloned repository does not contain an `AGENTS.md`, create one from the local repo's `AGENTS.md` or a minimal repository-specific template.
5. Report the created path and the remote URL used.
6. Update the workspace `reference-repos.md` index when the curated set of references changes.

## Notes

- Use the repository root of the current workspace, not the agent's own home directory.
- Keep reference repositories isolated under `.references/` so they can be inspected without affecting the main repo.
- When a reference repo already exists, treat it as a reusable local fixture rather than recreating it.
- Keep a `reference-repos.md` file in the workspace root with the repo URL, local clone path, and a short reason for keeping each reference.
```

## First session in the new repo

1. Brainstorm the open questions below with the owner, then write the spec (`docs/superpowers/specs/`) and the plan.
2. Scaffold: `galaxy.yml`, `plugins/modules/`, `plugins/module_utils/`, `tests/unit/`, `tests/integration/`, `meta/runtime.yml`, `CLAUDE.md`, `AGENTS.md`, `Makefile`, `.pre-commit-config.yaml`, `.gitignore` with `.references/`, `reference-repos.md`.
3. Add the reference repositories with the skill.
4. Build `opnsense_settings` first (simplest: get, compare, set, reconfigure) against one area, `nodeexporter/general`; then `opnsense_item` against `dnsmasq/settings` hosts.
5. Prove it against a real consumer playbook: replace one `uri` block in a branch, `--check --diff` shows `changed=0`.

## Open questions for the owner

| Question | Why it matters |
|---|---|
| Collection namespace and name (Galaxy namespaces allow no hyphen, e.g. `<namespace>.opnsense_mvc`) | fixes every FQCN in consumer playbooks |
| Licence: own code under MIT or GPL-3.0; code copied from `oxlorg.opnsense` would make it GPL-3.0 | decides whether borrowing is allowed |
| Public on GitHub and Galaxy, or private and pinned by git commit | private means no Galaxy release; public invites issues to answer |
| Test target for integration tests: a dedicated OPNsense VM on an isolated bridge (a second OPNsense on a shared bridge hands out DHCP and answers as the gateway) or a spare box | integration tests must never touch a production router |
| Which OPNsense versions to support: latest only, or latest plus the previous one during the upgrade window | sets the CI matrix |
