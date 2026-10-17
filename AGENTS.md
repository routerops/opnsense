# routerops.opnsense: standards

Single source of rules for every contributor and agent. `CLAUDE.md` imports this file.

Spec: `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`. Plans: `docs/superpowers/plans/` (start with the tracking file). Kickoff and its reasoning: `docs/kickoff.md`.

## Gate

`make venv` once, then `make check` before every commit: `ansible-lint` (production profile), `ansible-test sanity`, `ansible-test units`, gitleaks, `antsibull-changelog lint`, `reuse lint`. `make integration` runs only against the dedicated test VM (`docs/testing.md`), never against a production router.

## Rules

| Rule | Detail |
|---|---|
| Licences | `plugins/module_utils/` BSD-2-Clause, everything else GPL-3.0-or-later; every file starts with an `SPDX-FileCopyrightText: routerops.opnsense contributors` and an `SPDX-License-Identifier` comment, or is covered by `REUSE.toml`. No code copied from `oxlorg.opnsense` or `matthew-on-git/terraform-provider-opnsense`, facts and ideas only, each fact re-checked against `opnsense/core` or `opnsense/plugins`. Contributions under the DCO, no CLA |
| Dependencies | every dependency pinned to an exact version (`requirements-dev.txt`, `mise.toml`, actions by commit SHA); Renovate bumps them |
| API results | a write succeeds on `result == "saved"` (delete: `"deleted"`), an action on `status` `ok`; never trust the HTTP code; show `validations` and `status_msg` on failure |
| Module behaviour | check mode never writes; `changed` only on a real write; one apply per call, only after a write; `--diff` per field; secrets carry `no_log` and never reach a diff |
| Ansible style | see "Ansible" below |
| Tests | TDD: a test fails before the code exists; a new check or assert counts only after it failed once against a real fault; check mode must not fail on a fresh target, a rerun shows `changed=0` |
| Modules | full `DOCUMENTATION`, `EXAMPLES`, `RETURN`; generated tables are never edited by hand |
| Comments | see "Ansible" below |
| Docs | English; one fact in one place; tables over long lists; no hard-wrapped prose; ASCII `->` arrows |
| Changes | every user-visible change gets a fragment in `changelogs/fragments/`; commit at logical checkpoints; a human reviews every change |
| Confirm first | publishing to Galaxy, pushing tags, pushing to a shared branch, anything destructive or outward-facing |
| Language | code, comments, commits and docs in English; chat in the owner's language |

## Ansible

Every module, playbook and role follows Tier A (the official Ansible documentation: `ansible_tips_tricks.rst`, `collection_requirements.rst`, `developing_modules_best_practices.rst`, `developing_modules_documenting.rst`, the ansible-lint `production` profile) and Tier B (the Red Hat CoP [Automation Good Practices](https://github.com/redhat-cop/automation-good-practices)). There are no project rules on top of the two tiers. Tier B wins wherever it disagrees with Tier A. Where Tier B contradicts itself, this file picks one side: playbook files use `{verb}-{noun}.yml` with hyphens (CoP naming conventions), not `snake_case` (CoP coding style).

### Modules and collection

| Rule | Source | Enforced by |
|---|---|---|
| Python follows PEP 8; every function has a docstring and every file a header comment stating its intent; a function name says what it does | A, B | `pep8` sanity test; the rest by review |
| `DOCUMENTATION`: descriptions start with a capital and end with a period, `short_description` without one; check and diff mode under `attributes`, never `notes`; formatting macros (`O()`, `V()`, `RV()`, `C()`); FQCN in `seealso`; `version_added` is the quoted collection version | A | `validate-modules`; the rest by review |
| `EXAMPLES`: every task named, capitalised, no trailing period, FQCN, `true`/`false`, `state:` set where the module has a default, secrets start with `EXAMPLE`; each example is exercised by an integration test | A | review |
| Options shared by several modules live in one doc fragment under `plugins/doc_fragments/` | A | review |
| A `module_utils` file only the collection uses is marked internal and its name starts with `_`; making a public util private later is a breaking change | A | review |
| `no_log=True` on every secret option; `no_log=False` on an option whose name only looks secret; never ignore `validate-modules:no-log-needed` | A | `validate-modules` |
| Modules are idempotent and declarative (`present`/`absent`), return useful data even when nothing changed, and keep the return structure stable | A | unit and integration tests |
| Errors fail with a clear `msg` naming the field, path or value at fault; no traceback, no catch-all `except`, no `print`, `sys.exit()` or stderr | A, B | review |
| Every entry in `tests/sanity/ignore-*.txt` carries a reason; the `validate-modules` checks Tier A forbids ignoring are never ignored | A | review |
| Sanity and units run against every supported ansible-core release (`requires_ansible`) | A | CI matrix |
| SemVer: a patch release only fixes bugs, a minor release may add features and deprecations, only a major release breaks; the README states this, the supported ansible-core versions and the licences | A | review |

### Playbooks, tasks and roles

| Rule | Source | Enforced by |
|---|---|---|
| Avoid comments in playbooks; a descriptive task name says what a task does, and variables are explained in `defaults` and `vars` | B | review |
| FQCN for every module; every play, task and block named, capitalised, in the imperative, saying what it does | A, B | `fqcn`, `name[missing]`, `name[play]`, `name[casing]`, `name[unique]`; blocks and the imperative by review |
| No variable in a play name; no loop variable in a task name; any other variable only at the end of a task name | B | `name[template]` checks the position only; the rest by review |
| Bracket notation for key access: `x['stdout']`, not `x.stdout` | B | review |
| `\| bool` on a bare variable in `when`; `\| int`, `\| float` or `\| bool` on a caller-supplied variable before arithmetic or comparison | B | review |
| A YAML string containing `{` or `}` is tagged `!unsafe` (or `{{ '{{ x }}' }}` for one literal); a `.j2` template uses `{% raw %}` | A, B | review |
| `state:` set explicitly where the module has a default | A | review |
| A module instead of `command` or `shell` where one exists, `command` before `shell`; every `command` or `shell` task has a one-line comment saying why, `changed_when:`, and `check_mode:` where it only reads | A, B | `command-instead-of-module`, `command-instead-of-shell`, `no-changed-when`, `risky-shell-pipe`; the comment by review |
| File modes set and quoted; no `state: latest` | A | `risky-file-permissions`, `risky-octal`, `package-latest` |
| `no_log: true` on tasks a secret passes through; `diff: false` where a secret would land in a diff | A | review |
| `debug` tasks set a `verbosity:` that fits the message | B | review |
| YAML: two-space indent with indented list items, `.yml` not `.yaml`, YAML-style arguments not `key=value`, `>-` not `>`, a long `and` in `when` as a list, one space inside `{{ }}` | B | ansible-lint `yaml`; the rest by review |
| Beware of `ignore_errors: true`, especially in tests; avoid `set_fact` and use the smallest variable scope | B | review |
| Playbook files are named `{verb}-{noun}.yml` with hyphens, after what they do (`test-firewall-alias-item.yml`) | B | review |
| A role: lowercase name with `_`, no `-`; inputs in `defaults/main.yml` with the `<role>_` prefix, an input without a safe default left commented out; every input in `meta/argument_specs.yml`; internal variables (`register`, `set_fact`, `loop_var`) take `__<role>_`; task names in a file other than `main.yml` start with `<file stem> \| `; templates end in `.j2` and start with `{{ ansible_managed \| comment }}`; works in check mode; a `README.md` | A, B | `var-naming`, `role-name`; the rest by review |

## Confirm first

Never publish to Galaxy, push tags or run integration tests against anything but the dedicated test VM without the owner's confirmation.
