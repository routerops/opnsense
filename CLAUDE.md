# routerops.opnsense: standards

Single source of rules for every contributor and agent. `AGENTS.md` points here.

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
| Ansible style | FQCN everywhere; every task named in the imperative; bracket notation for key access (`x['stdout']`); `\| int` or `\| bool` before comparing a templated value; health checks match an expected answer; `no_log: true` on secret inputs, `diff: false` where a secret would land in a diff |
| Tests | TDD: a test fails before the code exists; a new check or assert counts only after it failed once against a real fault; check mode must not fail on a fresh target, a rerun shows `changed=0` |
| Modules | full `DOCUMENTATION`, `EXAMPLES`, `RETURN`; generated tables are never edited by hand |
| Comments | zero by default; one short line only for a non-obvious why; never restate the code or claim what you have not checked |
| Docs | English; one fact in one place; tables over long lists; no hard-wrapped prose; ASCII `->` arrows |
| Changes | every user-visible change gets a fragment in `changelogs/fragments/`; commit at logical checkpoints; a human reviews every change |
| Confirm first | publishing to Galaxy, pushing tags, pushing to a shared branch, anything destructive or outward-facing |
| Language | code, comments, commits and docs in English; chat in the owner's language |
