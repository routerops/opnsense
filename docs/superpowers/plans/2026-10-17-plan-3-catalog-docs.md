# Plan 3: Area catalog and generated docs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `meta/areas.yml` describes every area tested so far (Dnsmasq host, firewall alias, node_exporter general); `make docs` generates `docs/areas/<area>.md`, the README area table, the privileges table in `docs/testing.md` and every module `EXAMPLES` block from it; `make check` fails when a generated file is stale; every integration test reads its area from the catalog and runs the catalog example.

**Architecture:** The generator is an Ansible playbook (`tools/generate-docs.yml`) that runs on localhost with builtin modules only: `validate_argument_spec` checks each catalog entry, `template` renders the area pages, `blockinfile` replaces the marked blocks in `README.md`, `docs/testing.md` and the two module files. It always writes into an output tree (`build/docs/`); `make docs` copies that tree over the repository, `make docs-check` diffs it against the repository. Integration playbooks load the catalog with `vars_files` and take `path`, `key`, `lookup`, `actions`, `separators` and `apply` from their entry through `module_defaults`.

**Tech Stack:** as plan 2 (ansible-core 2.21.5, Python 3.12, ansible-lint 26.10.1, antsibull-changelog 0.35.1); Jinja templates; `diff` and `rsync`.

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, section "Area catalog and documentation". Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`. Depends on plan 2.

## Global Constraints

- Everything from plan 1 and plan 2 Global Constraints and `AGENTS.md` holds (SPDX headers, exact pins, FQCN, named and capitalised tasks, `{verb}-{noun}.yml`, `.yml`, bracket key access, `{% raw %}` for literal `{{ }}` in `.j2`, zero comments by default, English, no hard-wrapped prose, ASCII `->`).
- Generated files are never edited by hand; each starts with or is wrapped in a marker naming `meta/areas.yml` and `make docs`.
- `make check` fails when an example has no catalog entry or differs from the generated text, and when any generated file differs from the committed one (spec, "Module `EXAMPLES`" and "`make docs`" rows).
- A catalog entry, its integration test and its generated page land in the same change (spec).
- Integration tests run only against the test VM (`make integration-local`, approved by the owner); fixtures use invented values only (`example.test`, `192.0.2.0/24`).

### Catalog schema

`meta/areas.yml` holds one top-level key `opnsense_areas`, a dict keyed by entry id (`^[a-z0-9]+(_[a-z0-9]+)+$`, `<area>_<type>`). The integration test of an entry is `tests/integration/test-<id with _ -> ->-<module>.yml`.

| Key | Type | Required | Meaning |
|---|---|---|---|
| `area` | str | yes | page name: `docs/areas/<area>.md` |
| `title` | str | yes | section heading and README row (`Firewall alias`) |
| `module` | str, `item` or `settings` | yes | |
| `path` | str | yes | controller base path |
| `key` | str | yes | JSON wrapper key |
| `actions` | dict | no, `{}` | action name overrides |
| `lookup` | list of str | item only, required there | |
| `apply` | str | no, none | apply path |
| `write_only` | list of str | no, `[]` | field names OPNsense never returns |
| `ordered_fields` | list of str | no, `[]` | |
| `separators` | dict | no, `{}` | |
| `privileges` | list of dict (`name`, `title`, `acl`) | yes | API privilege, its GUI title, the `ACL.xml` it is read from |
| `min_version` | str | no | OPNsense floor above the release |
| `tested` | list of str | yes | OPNsense versions `make integration` passed on |
| `plugin` | str | no | plugin package |
| `stage` | str, `v0`, `0.x` or `v1` | yes | |
| `example` | dict: `name` + `items` (item) or `fields` (settings) | yes | the one example task |

Entries for this plan, values taken from the current playbooks, `docs/testing.md` and the module `EXAMPLES`:

| id | area | title | module | path | key | lookup | actions | separators | apply | privilege | plugin | example |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `dnsmasq_host` | dnsmasq | Dnsmasq host | item | `dnsmasq/settings` | `host` | `[host, domain]` | `searchHost`, `getHost`, `addHost`, `setHost`, `delHost` | | `dnsmasq/service/reconfigure` | `page-services-dnsforwarder` | | "Add a Dnsmasq host": `printer`, `example.test`, `192.0.2.10` |
| `firewall_alias` | firewall | Firewall alias | item | `firewall/alias` | `alias` | `[name]` | | `content: "\n"` | `firewall/alias/reconfigure` | `page-firewall-alias-edit` | | "Keep a host alias": `web_servers`, `host`, `[192.0.2.21, 192.0.2.22]`, `Web servers` |
| `nodeexporter_general` | nodeexporter | node_exporter general | settings | `nodeexporter/general` | `general` | | | | `nodeexporter/service/reconfigure` | `page-services-nodeexporter` | `os-node_exporter` | "Enable node_exporter on port 9100": `enabled: true`, `listenport: 9100` |

All three: `stage: v0`, `tested: ["26.7.7"]`. The Unbound example in `settings` has no tested entry and goes.

### Generator interface

`ansible-playbook -i localhost, tools/generate-docs.yml [-e opnsense_docs_catalog=<file>] [-e opnsense_docs_out=<dir>]`; defaults `meta/areas.yml` and `build/docs`, both relative to the repository root (`playbook_dir ~ '/..'`). Output tree mirrors the repository: `docs/areas/*.md`, `README.md`, `docs/testing.md`, `plugins/modules/item.py`, `plugins/modules/settings.py`. Values in generated YAML are rendered with `to_json` (JSON is YAML), so `"\n"`, `"0"` and `true` round-trip; entries are emitted in `dictsort` order.

| Make target | Does |
|---|---|
| `docs` | run the generator, `rsync -a --delete build/docs/docs/areas/ docs/areas/`, copy the four spliced files back |
| `docs-check` | run the generator, `diff -r build/docs/docs/areas docs/areas` and `diff` each spliced file; non-zero on any difference; part of `check` |

## Review Focus

- A misspelled catalog key (`seperators`): expect the generator to fail naming the entry and the key, never to drop the value silently (Task 1, unknown-key run).
- A string value that YAML would retype (`"\n"`, `"0"`, `"yes"`) in an example: expect the generated `EXAMPLES` to parse back to exactly the catalog value (Task 3, round-trip assert in the generator).
- A hand edit to a generated page, or a page left over from a removed entry: expect `make check` to fail (Task 2, hand-edit and stale-page runs).
- A catalog entry without its test playbook, or a test playbook without an entry: expect the generator to fail naming the file (Task 4).
- An area whose catalog `plugin` is not installed on the VM: expect the play to end with a skip message, not a failure (Task 4, fault copy with a wrong path).

---

### Task 1: Catalog and its validation

**Files:**
- Create: `meta/areas.yml`, `tools/generate-docs.yml`
- Modify: `Makefile` (`docs`, `docs-check` targets with the generator call only; `BIN ?=` so CI can pass its own), `galaxy.yml` (`build_ignore: tools`)

**Interfaces:**
- Produces: `opnsense_areas` (schema above); generator vars `opnsense_docs_catalog`, `opnsense_docs_out`; the play-level fact `opnsense_docs_entries` (`opnsense_areas | dict2items`, sorted by key) later tasks loop over.

- [ ] **Step 1: Run the missing target**

Run: `make docs-check`
Expected: FAIL, `No rule to make target 'docs-check'`.

- [ ] **Step 2: Write `meta/areas.yml`** with the three entries from Global Constraints (SPDX header, `---`).

- [ ] **Step 3: Write `tools/generate-docs.yml`, validation part**: load the catalog with `include_vars`; assert each id matches the id pattern; loop `ansible.builtin.validate_argument_spec` over the entries with the schema table as `argument_spec` (`choices` for `module` and `stage`, `required_if: [[module, item, [lookup]]]`), loop label = id; fail when a `settings` entry has `lookup` or `example.items`, or an `item` entry has `example.fields`. Add `docs` and `docs-check` targets that only run the generator for now.

- [ ] **Step 4: Prove the checks against faults**

Copy `meta/areas.yml` to the workspace three times: rename `separators` to `seperators` in `firewall_alias`; drop `lookup` from `dnsmasq_host`; set `module: items`. Run the generator with `-e opnsense_docs_catalog=<copy>` for each.
Expected: each run FAILS, the message names the entry id and the key (`seperators` as unsupported, `lookup` as missing, `module` with its choices).

- [ ] **Step 5: Run against the real catalog**

Run: `make docs-check && make lint`
Expected: generator ends `failed=0`; ansible-lint passes on `tools/generate-docs.yml` and `meta/areas.yml`.

- [ ] **Step 6: Commit** `meta/areas.yml tools/generate-docs.yml Makefile galaxy.yml` -> "Add area catalog and its validation".

### Task 2: Area pages, README table and privileges table

**Files:**
- Create: `tools/templates/area.md.j2`, `tools/templates/readme-areas.md.j2`, `tools/templates/testing-privileges.md.j2`, `docs/areas/dnsmasq.md`, `docs/areas/firewall.md`, `docs/areas/nodeexporter.md` (generated), `changelogs/fragments/area-catalog.yml`
- Modify: `tools/generate-docs.yml`, `Makefile`, `README.md`, `docs/testing.md`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: Task 1 `opnsense_docs_entries`, `opnsense_docs_out`.
- Produces: markers `<!-- {mark} areas: generated from meta/areas.yml by make docs -->` (README) and `<!-- {mark} privileges: generated from meta/areas.yml by make docs -->` (`docs/testing.md`), `{mark}` = `BEGIN`/`END`.

- [ ] **Step 1: Add the markers by hand**: an empty marker pair under a new README section `## Areas`; replace the `docs/testing.md` privileges table with a marker pair holding the current table verbatim.

- [ ] **Step 2: Run the check before the generator writes anything**

Run: `make docs-check`
Expected: FAIL, `build/docs/docs/areas` missing (diff on a missing directory).

- [ ] **Step 3: Implement the rendering**

Generator: `copy` the four spliced files into the output tree, `template` one page per distinct `area`, `blockinfile` the two Markdown blocks. Page: first line `<!-- Generated from meta/areas.yml by make docs; do not edit. -->`, `# <area>`, then per entry (in `dictsort` order) `## <title>`, a two-column table (Module, Path, Key, Actions, Lookup, Apply, Write-only fields, Ordered fields, Separators, Privileges, Minimum OPNsense, Tested on, Plugin, Stage; empty values shown as `-`, defaults as `default`) and the example task in a `yaml` fence, rendered by the same macro Task 3 uses for `EXAMPLES`. README block: table `Area | Item type | Module | Path | Stage | Tested on` linking each row to `docs/areas/<area>.md#<anchor>`. Testing block: `Test | Privilege | Source` with one row per privilege, test name from the id rule, `` `name` ("title", `api/<path first segment>/*`) `` as now. `make docs` and `make docs-check` as in the generator interface table; `check` depends on `docs-check`. CI job `check`: step "Check the generated docs" running `make docs-check BIN="$(dirname "$(command -v ansible-playbook)")"` on the 2.21.5 leg. Fragment `minor_changes`: area catalog and generated area pages.

- [ ] **Step 4: Generate and inspect**

Run: `make docs && git diff --stat && make docs-check`
Expected: three pages created; the README gains the table; the `docs/testing.md` privileges table is unchanged except formatting the template fixes; `docs-check` passes.

- [ ] **Step 5: Prove the check against faults**

Change one character in `docs/areas/firewall.md`, run `make docs-check`; restore. Create `docs/areas/stale.md`, run `make docs-check`; delete it.
Expected: both runs FAIL naming the file.

- [ ] **Step 6: Run the gate**

Run: `make check`
Expected: all parts pass (`reuse lint` covers the new `.md` through `REUSE.toml`; `.j2` files carry an SPDX header as a Jinja comment).

- [ ] **Step 7: Commit** -> "Generate area pages and tables from the catalog".

### Task 3: Generated module `EXAMPLES`

**Files:**
- Create: `tools/templates/examples.py.j2`
- Modify: `tools/generate-docs.yml`, `plugins/modules/item.py`, `plugins/modules/settings.py`, `docs/areas/*.md` (regenerated)

**Interfaces:**
- Consumes: Task 1 entries; Task 2 example macro (move it into `tools/templates/example.yml.j2` and import it from both templates).
- Produces: marker `# {mark} EXAMPLES: generated from meta/areas.yml by make docs` around the `EXAMPLES = r"""..."""` assignment in both modules.

- [ ] **Step 1: Wrap both `EXAMPLES` assignments in the marker pair by hand** and run `make docs-check`.
Expected: PASS (nothing generates the block yet).

- [ ] **Step 2: Add the module blocks to the generator, then run the check**

Generator: for each module, `blockinfile` the block rendered from its entries (connection lines `url: https://fw.example`, `api_key: "{{ opnsense_api_key }}"`, `api_secret: "{{ opnsense_api_secret }}"` inside `{% raw %}`; then `path`, `key`, `lookup` for item, `actions`, `ordered_fields`, `separators` only when non-empty, `apply` when set, then `items` or `fields`). After rendering, parse the block's string with `from_yaml` and assert, per entry, that `items` / `fields` and every option equal the catalog values; on mismatch fail naming the id.
Run: `make docs-check`
Expected: FAIL, both module files differ (quoting changes, the Unbound example removed).

- [ ] **Step 3: Prove the round-trip assert**

Copy the catalog, set `firewall_alias.example.items[0].fields.description` to `"yes"` and `separators.content` to `"\n"`; run the generator on the copy.
Expected: PASS, the rendered block shows `"yes"` quoted. Then break the macro on purpose (render a value without `to_json`) and rerun: FAIL naming `firewall_alias`; restore the macro.

- [ ] **Step 4: Generate and run the gate**

Run: `make docs && make check`
Expected: both `EXAMPLES` blocks regenerated, Unbound example gone, `validate-modules` passes, `docs-check` passes.

- [ ] **Step 5: Commit** -> "Generate module examples from the catalog".

### Task 4: Catalog-driven integration tests

**Files:**
- Rename: `tests/integration/test-nodeexporter-settings.yml` -> `tests/integration/test-nodeexporter-general-settings.yml`
- Modify: the three integration playbooks, `tools/generate-docs.yml`, `docs/testing.md` (`TARGET` example and verified runs use the new name; new verified-run rows), `docs/superpowers/plans/2026-10-17-v0-tracking.md` (plan 3 file name, status `done`)

**Interfaces:**
- Consumes: `opnsense_areas` through `vars_files: ../../meta/areas.yml`.
- Produces: the playbook pattern plan 4 copies: play var `opnsense_test_area: "{{ opnsense_areas['<id>'] }}"`; `module_defaults` take `path`, `key`, `apply` (`| default(none)`), and for item `lookup`, `actions | default({})`, `separators | default({})`, `ordered_fields | default([])`.

- [ ] **Step 1: Add the test-file checks to the generator, then run it**

Generator: fail when an entry's test file is missing or does not contain `opnsense_areas['<id>']`; fail when a `tests/integration/test-*.yml` matches no entry (`find` on the directory). Run `make docs-check`.
Expected: FAIL naming `test-nodeexporter-general-settings.yml` missing and `test-nodeexporter-settings.yml` without entry.

- [ ] **Step 2: Rename the node_exporter test and switch all three playbooks to the catalog**

Each playbook loses its literal `path`, `key`, `lookup`, `actions`, `separators`, `apply`. Each runs its catalog example twice (`items: "{{ opnsense_test_area['example']['items'] }}"` or `fields: "{{ opnsense_test_area['example']['fields'] }}"`) and asserts first not failed, second `changed == false`; item playbooks delete the example items in the `always` block (`items: "{{ opnsense_test_area['example']['items'] | map('combine', {'state': 'absent'}) }}"`); the settings playbook runs the example before restoring the original settings. A playbook whose entry has `plugin` starts with a check-mode read (`failed_when: false`) and `ansible.builtin.meta: end_play` when it failed with `the area or its plugin may be missing` in `msg`, after a `debug` (`verbosity: 0`) naming the plugin. Update `docs/testing.md`.
Run: `make docs-check && make lint`
Expected: PASS.

- [ ] **Step 3: Run the live suite**

Run: `make integration-reset`, then `make integration-local > <workspace>/integration.log 2>&1; tail -40 <workspace>/integration.log`
Expected: all three plays `failed=0`.

- [ ] **Step 4: Prove the new checks against faults**

Copy `test-firewall-alias-item.yml` outside the repository, change one example value in the second example run so it differs from the first; run it as `docs/testing.md` describes: FAIL on the idempotency assert. Copy `test-nodeexporter-general-settings.yml` with `opnsense_test_area` combined with `{'path': 'nodeexporterx/general'}`: the play ends with the skip message, `failed=0`. Roll the VM back.

- [ ] **Step 5: Ledger the runs and commit**

Add verified-run rows for the three tests (date, 26.7.7, result) to `docs/testing.md`, set plan 3 `done` in the tracking file, run `make check`.
Expected: PASS. Commit -> "Drive integration tests from the catalog".
