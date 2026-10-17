# Plan 3b: Field reference per area Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every generated area page lists the fields a call can send (name, type, required, default, allowed values), read from the OPNsense model XML at the tested version, and the generator fails when a catalog example names a field the model lacks; an area can carry several examples, the module `EXAMPLES` cover add, delete and purge, and a full area table lives in `docs/areas/README.md` with a short per-area list in the README.

**Architecture:** A pure extractor (`tools/extract-fields.sh`, `yq` on XML) turns one model node into a YAML field list; `make fields` downloads each entry's model XML from `raw.githubusercontent.com` at the entry's newest tested version and writes `meta/fields/<id>.yml` (committed, so `make docs` and CI stay offline). The docs generator reads those files, checks them against the catalog and renders a field table per section.

**Tech Stack:** as plan 3, plus `yq` 4.54.1 (pinned in `mise.toml`) and `curl`.

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, "Area catalog and documentation" ("the area documentation carries that knowledge, as the per-resource pages do in `matthew-on-git/terraform-provider-opnsense/docs/`"). Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`. Depends on plan 3 (PR #3).

## Global Constraints

- Everything from plan 3 Global Constraints and `AGENTS.md` holds.
- Source of every field fact: the model XML in `opnsense/core` or `opnsense/plugins` (BSD-2-Clause) at the git tag equal to the version (`26.7.7` exists in both). Only facts are taken: field name, type, required, default, multiple, option values. No prose (no `ValidationMessage`, no option labels, no form help texts). Nothing from `matthew-on-git/terraform-provider-opnsense` or `oxlorg.opnsense`.
- `make fields` needs network and runs only locally; `make docs`, `make docs-check` and CI never touch the network.
- Data handling: `yq` and shell only, no Python (owner rule: jq/yq/awk for parsing).
- `tools/extract-fields.sh` has no shebang and no executable bit; the Makefile runs it with `bash`. It starts with an SPDX header and a header comment (where it runs, input, output).

### Model XML facts (26.7.7)

| Fact | Detail |
|---|---|
| Field | an element with a `type` attribute (`yq -p xml`: key `+@type`) |
| Type name | the attribute value with a leading `.\` and any namespace prefix up to the last `\` removed (`.\AliasNameField` -> `AliasNameField`) |
| Required | child `<Required>Y</Required>` |
| Default | child `<Default>`; absent -> no default |
| Multiple | child `<Multiple>Y</Multiple>` |
| Option values | children of `<OptionValues>`; the stored value is the child's `value` attribute when present (`<unreach value="1">`), else the element name |
| Runtime-only field | attribute `volatile="true"` (`current_items`, `last_updated` in `Alias.xml`); never stored, listed with `volatile: true` and shown as "not stored" (Trust CA and certificate create inputs are volatile) |
| Container | an element without `type` whose children are fields: its fields are named `<container>.<field>` |
| Nested list | a field of type `ArrayField` inside an item: listed as one field of that type, not expanded |

Entry model locations:

| id | repo | file | node below `model.items` |
|---|---|---|---|
| `dnsmasq_host` | core | `src/opnsense/mvc/app/models/OPNsense/Dnsmasq/Dnsmasq.xml` | `hosts` |
| `firewall_alias` | core | `src/opnsense/mvc/app/models/OPNsense/Firewall/Alias.xml` | `aliases.alias` |
| `nodeexporter_general` | plugins | `sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/General.xml` | none (the items root) |

### Interfaces

- Catalog key `model` (required): dict `repo` (`core` or `plugins`), `file` (str), `node` (str, optional; absent = items root).
- `bash tools/extract-fields.sh <xml file> [<node>]` -> YAML on stdout: a list of `{name, type, required, default, multiple, options}` (`default` omitted when absent, `options` `[]` when none), in document order.
- `meta/fields/<id>.yml`: SPDX header, `# Generated from the OPNsense model XML by make fields; do not edit.`, then `version` (str), `source` (`opnsense/<repo>@<version>:<file>#<node>`), `fields` (the extractor list).
- `make fields [ID=<id>]`: for each entry (or one), `curl -fsSL https://raw.githubusercontent.com/opnsense/<repo>/<version>/<file>` with `<version>` = last item of `tested`, extract, write the file.
- `make fields-test`: runs the extractor on each `tools/tests/fields/*.xml` and diffs against the matching `.expected.yml`; part of `make check`, not of CI (CI has no pinned `yq`).

## Review Focus

- An option with a `value` attribute (`<unreach value="1">`): expect `1` in `options`, not `unreach` (Task 1, fixture `options-value`).
- A runtime-only field (`volatile="true"`): expect it listed with `volatile: true` and shown as "not stored" (Task 1, fixture `volatile`).
- A catalog example that names a field the model lacks (`descriptoin`): expect the generator to fail naming entry and field, offline (Task 2).
- A fields file left at an older version after `tested` gains a new one: expect the generator to fail naming the entry and both versions (Task 2).
- A model node path that matches nothing (typo in `node`): expect `make fields` to fail naming the entry, not to write an empty field list (Task 2).
- An example list where a later example undoes an earlier one (add, then delete): expect each example to run twice in a row and the second run to show `changed=0`, never a pass over all examples twice (Task 4).
- `purge: true` in an example: expect it only on an area without built-in rows, so the integration run deletes nothing it did not create (Task 4, purge example on `dnsmasq_host` only).

---

### Task 1: Field extractor

**Files:**
- Create: `tools/extract-fields.sh`, `tools/tests/fields/flat.xml`, `flat.expected.yml`, `options-value.xml`, `options-value.expected.yml`, `volatile.xml`, `volatile.expected.yml`, `container.xml`, `container.expected.yml`, `root.xml`, `root.expected.yml` (fixtures invented, a few fields each, shaped after the facts table)
- Modify: `Makefile` (`fields-test`, added to `check`)

**Interfaces:**
- Produces: the extractor contract above.

- [ ] **Step 1: Write the fixtures and `fields-test`, then run it**

Fixtures: `flat` (node `items.things`: a `BooleanField` with `Default` 1 and `Required` Y, an `OptionField` with `Multiple` Y and two options, a `.\NameField`, a `TextField` with nothing set); `options-value` (one `OptionField` whose options carry `value` attributes); `volatile` (one stored, one `volatile="true"` field); `container` (an untyped `source` element with `network` and `port` fields, plus a nested `ArrayField` with children); `root` (singleton, no node). Each `.expected.yml` written by hand from the facts table. The node per fixture is the first line of the XML as a comment `<!-- node: things -->` (empty for `root`).
Run: `make fields-test`
Expected: FAIL, `tools/extract-fields.sh` missing.

- [ ] **Step 2: Implement `tools/extract-fields.sh`** with `yq -p xml` per the facts table; fail with a message naming the node when it resolves to nothing.

- [ ] **Step 3: Run the tests**

Run: `make fields-test`
Expected: PASS, every fixture diff empty. Then break the `value` handling on purpose: `options-value` FAILS; restore.

- [ ] **Step 4: Gate and commit**

Run: `make check`
Expected: PASS. Commit -> "Add the model field extractor".

### Task 2: Field files and catalog checks

**Files:**
- Create: `meta/fields/dnsmasq_host.yml`, `meta/fields/firewall_alias.yml`, `meta/fields/nodeexporter_general.yml` (generated)
- Modify: `meta/areas.yml` (`model` per entry, values from the location table), `tools/generate-docs.yml` (schema key `model`; checks below), `Makefile` (`fields`)

**Interfaces:**
- Consumes: Task 1 extractor.
- Produces: `meta/fields/<id>.yml`; generator var `opnsense_docs_fields` (dict id -> fields file content) loaded with `include_vars` per entry.

- [ ] **Step 1: Add the generator checks, then run them**

Generator, per entry: fail when `meta/fields/<id>.yml` is missing; when its `version` differs from the last `tested` item (message names both); when an example field name (`example.fields` or each `example.items[].fields`) or a `write_only` name is not among the file's field names (message names the entry and the field).
Run: `make docs-check`
Expected: FAIL, the three field files missing.

- [ ] **Step 2: Add `model` to the catalog and implement `make fields`**

Run: `make fields`
Expected: three files written, `version: "26.7.7"`. Inspect: `firewall_alias` lists `enabled`, `name`, `type` (options include `host`, `network`, `port`), `content`, `description`, no `current_items`; `dnsmasq_host` lists `host`, `domain`, `ip`, `hwaddr`, `descr`, `aliases`; `nodeexporter_general` lists `enabled` (default `0`), `listenport` (default `9100`). If a name the integration tests use is missing, the node is wrong: fix the catalog, not the file.

- [ ] **Step 3: Prove the checks against faults**

Scratch catalog copies: `description` -> `descriptoin` in the `firewall_alias` example; `tested: ["26.7.7", "26.7.8"]` in `dnsmasq_host`; run the generator on each. Then `make fields ID=firewall_alias` with `node: aliases.alis` in a scratch catalog (pass the catalog path through a `CATALOG` make variable).
Expected: all three FAIL naming the entry (and the field, both versions, or the node).

- [ ] **Step 4: Gate and commit**

Run: `make docs-check && make check`
Expected: PASS. Commit -> "Extract area fields from the OPNsense models".

### Task 3: Field tables on the area pages

**Files:**
- Modify: `tools/templates/area.md.j2`, `docs/areas/*.md` (regenerated)

**Interfaces:**
- Consumes: Task 2 `opnsense_docs_fields`.

- [ ] **Step 1: Change the template, then run the check**

After each section's settings table and before the example: `### Fields` with the line `Read from <source>.`, then `| Field | Type | Required | Default | Values |`, one row per field in file order: name in backticks, a `(write-only)` suffix for `write_only` names, `Type` the OPNsense type plus `, multiple` when set, `Required` `yes` or empty, `Default` in backticks or empty, `Values` the options in backticks joined by `, ` or empty.
Run: `make docs-check`
Expected: FAIL, the three pages differ.

- [ ] **Step 2: Generate and inspect**

Run: `make docs && make docs-check`
Expected: PASS; `docs/areas/firewall.md` shows `type` with `host`, `network` among its values and no `current_items`.

- [ ] **Step 3: Gate and commit**

Run: `make check`
Expected: PASS. Commit -> "List each area's fields on its page".

### Task 4: Several examples per area, with delete and purge

**Files:**
- Modify: `meta/areas.yml` (`example` -> `examples`), `tools/generate-docs.yml` (schema, name check, field-name check from Task 2, round-trip check: all per example), `tools/templates/example.yml.j2`, `tools/templates/area.md.j2`, `tools/templates/examples.py.j2`, `tools/templates/example-check.yml.j2`, the three integration playbooks, `plugins/modules/item.py` and `settings.py` and `docs/areas/*.md` (regenerated)

**Interfaces:**
- Consumes: Task 2 field-name check; plan 3 macro `example_task`.
- Produces: catalog key `examples` (required, list, at least one) of `{name, items | fields, purge}`; `purge` (bool) only on item entries; macro `example_task(e, x)` (entry, one example) that emits `purge: true` before `items` when set.

Catalog examples after this task (values invented):

| id | name | content |
|---|---|---|
| `dnsmasq_host` | Add a Dnsmasq host | as now (`printer`) |
| `dnsmasq_host` | Keep only the listed Dnsmasq hosts | `purge: true`, items `printer` and `scanner` (`192.0.2.11`), both `example.test` |
| `dnsmasq_host` | Remove a Dnsmasq host | `scanner` with `state: absent` |
| `firewall_alias` | Keep a host alias | as now (`web_servers`) |
| `firewall_alias` | Keep a port alias | `web_ports`, type `port`, content `["80", "443"]`, description `Web ports` |
| `nodeexporter_general` | Enable node_exporter on port 9100 | as now |

No `purge` example on `firewall_alias`: its search lists built-in aliases (plan 2 facts).

- [ ] **Step 1: Switch the playbooks to the example list, then run the check**

Each playbook runs its examples with `loop: "{{ opnsense_test_area['examples'] | product([1, 2]) | list }}"` (each example twice in a row, `purge` from `item[0]['purge'] | default(false)`), registers the loop, and asserts that every result whose `item[1] == 2` has `changed == false`. The `always` block removes the items of every example with `state: absent`.
Run: `make lint`
Expected: PASS. The playbooks read `examples`, which the catalog does not have yet; the live run in Step 4 is their test.

- [ ] **Step 2: Change the catalog and the generator, then run the check**

Catalog to the table above. Schema: `examples` (list of dict, required) with the option set of the former `example` plus `purge` (bool); assert at least one example, `purge` only on item entries; run the name check, the Task 2 field-name check and the round-trip check per example (loop over `subelements`, label `<id>: <example name>`). Macro and templates loop over the examples; a page shows all examples of a section in one `yaml` fence, separated by a blank line.
Run: `make docs-check`
Expected: FAIL, pages and both `EXAMPLES` blocks differ (new examples, `purge: true` in the item block).

- [ ] **Step 3: Prove the new checks against faults**

Scratch catalogs: `examples: []` on `firewall_alias`; `purge: true` on `nodeexporter_general`'s example; `purge: "yes please"`.
Expected: each FAILS naming the entry (and the example where one exists).

- [ ] **Step 4: Generate, gate, run live**

Run: `make docs && make check`, then `make integration-reset && make integration-local`, then `make integration-reset`.
Expected: `make check` PASS; all three plays `failed=0`; the dnsmasq play shows the purge example adding `scanner` without purging anything on its first run.

- [ ] **Step 5: Commit** -> "Allow several examples per area".

### Task 5: Area overview, spec and tracking

**Files:**
- Create: `tools/templates/areas-index.md.j2`, `docs/areas/README.md` (generated), `changelogs/fragments/area-fields.yml`
- Modify: `tools/generate-docs.yml`, `tools/templates/readme-areas.md.j2`, `README.md` (regenerated), `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`, `docs/superpowers/plans/2026-10-17-v0-tracking.md`

**Interfaces:**
- Consumes: catalog keys `plugin`, `min_version`.

- [ ] **Step 1: Change the templates, then run the check**

`docs/areas/README.md`: first line the generated-file comment, `# Areas`, then `| Area | Item type | Module | Path | Plugin | Minimum OPNsense | Stage | Tested on |`, one row per entry sorted by id, links relative (`dnsmasq.md#dnsmasq-host`), empty values `-`. README block: `| Area | Item types |`, one row per area, item types as links to their sections joined by `, `, then the line `All item types with plugin, version and stage: [docs/areas/README.md](docs/areas/README.md).`
Run: `make docs-check`
Expected: FAIL, `docs/areas/README.md` missing and the README block differs.

- [ ] **Step 2: Generate and check**

Run: `make docs && make docs-check`
Expected: PASS; the node_exporter row shows `os-node_exporter` as plugin.

- [ ] **Step 3: Spec, tracking, fragment**

Spec, "Area catalog and documentation": the catalog row gains `model` and `examples` (one or more); the `docs/areas/<area>.md` row says one section per item type with the values above, the field table read from the model XML at the newest tested version, and the examples; a new row `docs/areas/README.md` (full area table; the README shows one row per area); the `Module EXAMPLES` row adds that they cover add, delete and purge; a sentence on `make fields` (local, network, rerun when `tested` gains a version). Tracking: insert row `3b` between 3 and 4, status `done`. Fragment `minor_changes`: area pages list each area's fields from the OPNsense model, and the module examples show delete and purge.

- [ ] **Step 4: Gate and commit**

Run: `make check`
Expected: PASS. Commit -> "Add the area overview and record plan 3b".
