# Plan 1: Foundation and `settings` module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A scaffolded `routerops.opnsense` collection whose `make check` passes, with a tested HTTP client, field normalisation and a working `routerops.opnsense.settings` module proven against `nodeexporter/general`.

**Architecture:** The repository root is the collection root. `make` copies it into `build/ansible_collections/routerops/opnsense` because `ansible-test` only runs inside that path. Shared code lives in three `module_utils` files (client, fields, common), and the `settings` module composes them. Unit tests replace the client with a fake; the integration test runs a playbook against the test VM.

**Tech Stack:** ansible-core 2.21.5 (CI also 2.20.10), Python 3.12, ansible-test (sanity, units), ansible-lint 26.10.1, gitleaks v8.30.1, pre-commit 4.7.0, GitHub Actions (`actions/checkout` v7.0.1, `actions/setup-python` v7.0.0).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`. Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`.

## Global Constraints

- Collection `routerops.opnsense`; `plugins/module_utils/` BSD-2-Clause, everything else GPL-3.0-or-later; every file starts with `# Copyright: routerops.opnsense contributors` and `# SPDX-License-Identifier: <licence>` (or the `.license` sidecar / `REUSE.toml` entry for files without comments); `requires_ansible: ">=2.20.0"` (2.19 is EOL on 30.11.2026, endoflife.date).
- Every dependency pinned to an exact version: `ansible-core==2.21.5`, `ansible-lint==26.10.1`, gitleaks `v8.30.1`, pre-commit `4.7.0`, actions by full commit SHA (`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`, `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`).
- `validate_certs` defaults to `true`; `api_key` and `api_secret` carry `no_log`.
- Success of a write is `result == "saved"`, of an action `status == "ok"` (case-insensitive), never the HTTP code; a failure shows the `validations` map.
- Check mode never writes; `changed` only on a real write; the apply call runs once per module call and only after a write.
- English for code, docs and commits; zero comments by default; no hard-wrapped prose; FQCN everywhere; `ansible-lint` production profile.
- Never commit `.references/` or `build/`.

## Review Focus

- A field name the caller misspells: expect the task to fail naming the field, never a silent `changed` on every run (Task 5, `test_unknown_field_fails`).
- An option field with several selected values compared in a different order: expect no change (Task 4, `test_normalize_list_ignores_order`).
- A write-only value (password, token): expect it absent from `diff` and from the returned settings (Task 5, `test_write_only_absent_from_diff_and_result`).
- The API answers HTTP 200 with `{"result": "failed"}`: expect a failed task carrying the validations (Task 3, `test_require_saved_raises_with_validations`; Task 5, `test_failed_validation_fails_with_validations`).
- The API answers non-JSON (an HTML login page after a wrong URL): expect a failed task naming the URL, not a traceback (Task 3, `test_non_json_response_raises`).

---

### Task 1: Scaffold and the `make check` gate

**Files:**
- Create: `galaxy.yml`, `meta/runtime.yml`, `LICENSES/GPL-3.0-or-later.txt`, `LICENSES/BSD-2-Clause.txt` (both via `reuse download`), `REUSE.toml` (covers JSON, `.keep` and other files without comments), `README.md`, `.gitignore`, `.ansible-lint`, `requirements-dev.txt`, `Makefile`, `.pre-commit-config.yaml`, `renovate.json`, `CLAUDE.md`, `AGENTS.md`, `reference-repos.md`, `.agents/skills/add-reference-repository/SKILL.md`, symlink `.claude/skills` -> `../.agents/skills`, `plugins/modules/.keep`, `plugins/module_utils/.keep`, `tests/unit/.keep`, `tests/integration/.keep`, `changelogs/.keep`

**Interfaces:**
- Produces: make targets `venv`, `collection-tree`, `lint`, `sanity`, `units`, `secrets`, `check`, `integration`; build path `build/ansible_collections/routerops/opnsense`.

- [ ] **Step 1: Write the metadata files**

`galaxy.yml`: `namespace: routerops`, `name: opnsense`, `version: 0.1.0`, `license: [GPL-3.0-or-later, BSD-2-Clause]`, `repository: https://github.com/routerops/opnsense`, `build_ignore: [build, .references, .venv, .agents, .claude, docs/superpowers]`. `meta/runtime.yml`: `requires_ansible: ">=2.20.0"` and `action_groups: {opnsense: [settings]}`. `.gitignore`: `.references/`, `build/`, `.venv/`, `*.pyc`, `tests/output/`. `.editorconfig`: UTF-8, LF, final newline, trim trailing whitespace, 2-space indent for YAML, 4 for Python. `.ansible-lint`: `profile: production`, `exclude_paths: [build/, .references/, .venv/]`. `requirements-dev.txt`: `ansible-core==2.21.5`, `ansible-lint==26.10.1`, `pre-commit==4.7.0`, `antsibull-changelog==0.35.1`, `reuse==6.2.0`. Then `antsibull-changelog init .` creates `changelogs/config.yaml` and `changelogs/fragments/` (replaces `changelogs/.keep`). `renovate.json`: `{"extends": ["config:recommended"], "pip_requirements": {"fileMatch": ["requirements-dev\\.txt$"]}}`.

- [ ] **Step 2: Write the `Makefile`**

| Target | Command |
|---|---|
| `venv` | `python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` |
| `collection-tree` | `rsync -a --delete --exclude build --exclude .references --exclude .venv --exclude .git ./ build/ansible_collections/routerops/opnsense/` |
| `lint` | `.venv/bin/ansible-lint` |
| `sanity` | depends on `collection-tree`; `cd build/ansible_collections/routerops/opnsense && ansible-test sanity --venv --python 3.12` |
| `units` | depends on `collection-tree`; `cd build/ansible_collections/routerops/opnsense && ansible-test units --venv --python 3.12` |
| `secrets` | `gitleaks git --no-banner` |
| `changelog-lint` | `.venv/bin/antsibull-changelog lint` |
| `licences` | `.venv/bin/reuse lint` |
| `check` | `lint sanity units secrets changelog-lint licences` (plan 3 adds the docs freshness check) |
| `integration` | fails with `set OPNSENSE_INTEGRATION=1` unless that variable is `1`; fails unless `OPNSENSE_URL`, `OPNSENSE_API_KEY`, `OPNSENSE_API_SECRET` are set; then `ANSIBLE_COLLECTIONS_PATH=$(CURDIR)/build ansible-playbook tests/integration/$(or $(TARGET),*).yml` per file |

`ansible-test` runs from `.venv/bin` (prepend it to `PATH` in the Makefile). `--venv` instead of `--docker` locally is the assistant's call: no Docker requirement on the owner's machine.

- [ ] **Step 3: Write the agent and reference files**

`CLAUDE.md` holds the standards: the Global Constraints above, the gate (`make check`), the spec path, "confirm before publishing to Galaxy or pushing tags", "integration tests only against the dedicated test VM", the tables "Ansible lessons" and "Working agreements to keep" from `docs/kickoff.md` (bracket notation for key access, `| int`/`| bool` before comparing, health checks match an expected answer, a check counts only after it failed once, `no_log`/`diff: false` for secrets, chat in the owner's language, human review of every change). `AGENTS.md` says in two lines that `CLAUDE.md` is the standard and repeats the two confirm rules. The skill file is copied verbatim from `docs/kickoff.md`, section "Reference repositories". `reference-repos.md` holds the four-row table from the same section plus a "Local path" column (`.references/<name>`). `.pre-commit-config.yaml` runs `gitleaks` at `v8.30.1` and `ansible-lint` at `v26.10.1`.

- [ ] **Step 4: Run the gate**

Run: `make venv && make check`
Expected: exits 0; sanity reports no errors on the empty collection.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Scaffold routerops.opnsense collection and make check gate"
```

### Task 2: Reference repositories

**Files:**
- Modify: `reference-repos.md` (only if a URL or reason changes)

- [ ] **Step 1: Clone the four references with the `add-reference-repository` skill**

`opnsense-core`, `opnsense-plugins`, `ansible-opnsense`, `terraform-provider-opnsense`, URLs from `reference-repos.md`, into `.references/<name>` with `--depth 1`.

- [ ] **Step 2: Verify**

Run: `ls .references && git status --short`
Expected: four directories; `git status` shows nothing under `.references/`.

No commit unless `reference-repos.md` changed.

### Task 3: HTTP client

**Files:**
- Create: `plugins/module_utils/client.py`
- Test: `tests/unit/plugins/module_utils/test_client.py`

**Interfaces:**
- Produces:
  - `class OPNsenseError(Exception)` with `__init__(self, msg: str, validations: dict | None = None, status: int | None = None)` and attributes `msg`, `validations`, `status`.
  - `class OPNsenseClient` with `__init__(self, url: str, api_key: str, api_secret: str, validate_certs: bool = True, timeout: int = 30)`, `get(self, path: str) -> dict`, `post(self, path: str, payload: dict | None = None) -> dict`. `path` is relative to `<url>/api/`, e.g. `nodeexporter/general/get`.
  - `require_saved(response: dict) -> None` and `require_ok(response: dict) -> None`, both raising `OPNsenseError`.

- [ ] **Step 1: Write the failing tests**

Patch `open_url` in the module under test (`monkeypatch.setattr(client, "open_url", fake)`); `fake` records its arguments and returns an object whose `read()` returns the given bytes.

```python
def test_get_builds_url_and_basic_auth(monkeypatch): ...
    # OPNsenseClient("https://fw.example", "k", "s").get("nodeexporter/general/get")
    # -> open_url called with url "https://fw.example/api/nodeexporter/general/get",
    #    method "GET", url_username "k", url_password "s", force_basic_auth True, validate_certs True
def test_post_sends_json_body(monkeypatch): ...
    # post("x/y/set", {"a": "1"}) -> method "POST", data == b'{"a": "1"}', header Content-Type application/json
def test_post_without_payload_sends_empty_object(monkeypatch): ...  # data == b'{}'
def test_trailing_slash_in_url_is_ignored(monkeypatch): ...  # "https://fw.example/" -> ".../api/..."
def test_http_error_raises_with_status(monkeypatch): ...  # fake raises HTTPError 403 -> OPNsenseError.status == 403
def test_non_json_response_raises(monkeypatch): ...  # read() -> b"<html>" -> OPNsenseError, msg contains the full URL
def test_require_saved_accepts_saved(): require_saved({"result": "saved"})
def test_require_saved_raises_with_validations():
    with pytest.raises(OPNsenseError) as e:
        require_saved({"result": "failed", "validations": {"general.listenport": "bad"}})
    assert e.value.validations == {"general.listenport": "bad"}
def test_require_ok_accepts_any_case_and_whitespace(): require_ok({"status": "OK"}); require_ok({"status": " ok\n"})
def test_require_ok_raises_with_status_msg(): ...  # {"status": "failed", "status_msg": "boom"} -> OPNsenseError, "boom" in msg
def test_not_found_names_path(monkeypatch): ...  # HTTPError 404 -> OPNsenseError.status == 404, msg contains the path and "plugin"
def test_endpoint_not_found_body_names_path(monkeypatch): ...  # 200 with {"errorMessage": "Endpoint not found"} -> same error as 404
def test_get_retries_three_times_on_5xx(monkeypatch): ...  # two HTTPError 502, then success -> result returned, 3 calls
def test_get_gives_up_after_three_attempts(monkeypatch): ...  # four 502 -> OPNsenseError after 3 calls
def test_post_never_retries(monkeypatch): ...  # HTTPError 502 on POST -> OPNsenseError after 1 call
```

- [ ] **Step 2: Run to verify they fail**

Run: `make units`
Expected: FAIL, `ModuleNotFoundError` for `client`.

- [ ] **Step 3: Implement `plugins/module_utils/client.py`**

Use `ansible.module_utils.urls.open_url` and `ansible.module_utils.six.moves.urllib.error.HTTPError`; `json.loads` on the body; any `ValueError` or `HTTPError` becomes `OPNsenseError`. GET retries on `URLError` or HTTP 5xx, three attempts in total, one second apart; POST never retries (spec). `from __future__ import annotations` at the top of every `module_utils` and module file, because sanity compiles for every target Python the ansible-core version supports. Header: `# Copyright: routerops.opnsense contributors` and `# SPDX-License-Identifier: BSD-2-Clause` (module_utils); modules and tests use `GPL-3.0-or-later`.

- [ ] **Step 4: Run to verify they pass**

Run: `make units sanity`
Expected: PASS, sanity clean.

- [ ] **Step 5: Commit**

```bash
git add plugins/module_utils/client.py tests/unit/plugins/module_utils/test_client.py
git commit -m "Add OPNsense API client with result checks"
```

### Task 4: Field normalisation and diff

**Files:**
- Create: `plugins/module_utils/fields.py`
- Test: `tests/unit/plugins/module_utils/test_fields.py`

**Interfaces:**
- Produces:
  - `normalize(read: Any, wanted: Any, ordered: bool = False, separator: str = ",") -> Any`: the read value in the caller's plain form, shaped by the type of `wanted`.
  - `to_api(wanted: Any, separator: str = ",") -> Any`: the caller's value as the API expects it; a dict is converted value by value.
  - `field_diff(current: dict, wanted: dict, ordered_fields: tuple = (), separators: dict | None = None) -> dict[str, tuple[Any, Any]]`: `{field: (normalised_before, wanted)}` for every differing field; a nested dict in `wanted` recurses and reports dotted names (`source.network`); raises `KeyError(field)` for a field missing in `current`.
  - `nest_fields(flat: dict) -> dict`: turns dotted names back into nested dicts for the payload.

Rules (spec, "Both modules"): an option map is a dict whose values are dicts with a `selected` key; its selected keys are those with `selected` in `(1, "1", True)`, the key `""` is dropped. `[]` and `None` read as no selection. `wanted` is `bool` -> `True` only for `"1"`, `1`, `True`; `wanted` is `int` -> `int(read)`, `""` -> `None`; `wanted` is `list` -> selected keys (or the string split on `separator`), sorted unless `ordered`; otherwise a string (option map -> selected keys joined with `separator`). `to_api`: `True`/`False` -> `"1"`/`"0"`, list -> joined with `separator`, `int` -> `str`, `None` -> `""`.

- [ ] **Step 1: Write the failing tests**

```python
def test_normalize_bool(): assert normalize("1", True) is True and normalize("0", True) is False
def test_normalize_int(): assert normalize("9100", 9100) == 9100 and normalize("", 1) is None
def test_normalize_single_option():
    assert normalize({"a": {"value": "A", "selected": 0}, "b": {"value": "B", "selected": 1}}, "b") == "b"
def test_normalize_multi_option():
    assert normalize({"a": {"selected": 1}, "b": {"selected": 1}, "c": {"selected": 0}}, ["a", "b"]) == ["a", "b"]
def test_normalize_list_ignores_order():
    assert field_diff({"x": {"a": {"selected": 1}, "b": {"selected": 1}}}, {"x": ["b", "a"]}) == {}
def test_normalize_comma_string_as_list(): assert normalize("a,b", ["b", "a"]) == ["a", "b"]
def test_to_api():
    assert [to_api(True), to_api(False), to_api(["a", "b"]), to_api(9100), to_api(None), to_api("x")] == ["1", "0", "a,b", "9100", "", "x"]
def test_field_diff_reports_only_differences():
    assert field_diff({"enabled": "0", "listenport": "9100"}, {"enabled": True, "listenport": 9100}) == {"enabled": (False, True)}
def test_field_diff_missing_field_raises():
    with pytest.raises(KeyError): field_diff({"enabled": "0"}, {"enabeld": True})
def test_normalize_empty_select_forms():
    assert normalize([], "") == "" and normalize(None, []) == [] and normalize({"": {"value": "none", "selected": 1}, "a": {"selected": 0}}, "") == ""
def test_normalize_string_field_returned_as_option_map():
    assert normalize({"10.0.0.5": {"value": "10.0.0.5", "selected": 1}}, "10.0.0.5") == "10.0.0.5"
def test_ordered_field_keeps_order():
    assert field_diff({"t": "10.0.0.2/32,10.0.0.1/32"}, {"t": ["10.0.0.1/32", "10.0.0.2/32"]}, ordered_fields=("t",)) != {}
def test_separator_per_field():
    assert field_diff({"content": "a\nb"}, {"content": ["b", "a"]}, separators={"content": "\n"}) == {}
    assert to_api(["a", "b"], "\n") == "a\nb"
def test_nested_fields_diff_and_nest():
    d = field_diff({"source": {"network": "any", "port": "", "not": "0"}}, {"source": {"network": "lan", "not": False}})
    assert d == {"source.network": ("any", "lan")}
    assert nest_fields({"source.network": "lan"}) == {"source": {"network": "lan"}}
```

- [ ] **Step 2: Run to verify they fail**

Run: `make units`
Expected: FAIL, `ModuleNotFoundError` for `fields`.

- [ ] **Step 3: Implement the four functions in `plugins/module_utils/fields.py`**

- [ ] **Step 4: Run to verify they pass**

Run: `make units sanity`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/module_utils/fields.py tests/unit/plugins/module_utils/test_fields.py
git commit -m "Add field normalisation and diff"
```

### Task 5: `settings` module

**Files:**
- Create: `plugins/module_utils/common.py`, `plugins/modules/settings.py`
- Modify: `plugins/modules/.keep` (delete), `plugins/module_utils/.keep` (delete)
- Test: `tests/unit/plugins/modules/conftest.py`, `tests/unit/plugins/modules/test_settings.py`

**Interfaces:**
- Consumes: Task 3 `OPNsenseClient`, `OPNsenseError`, `require_saved`, `require_ok`; Task 4 `normalize`, `field_diff`, `to_api`.
- Produces:
  - `common.CONNECTION_ARGSPEC: dict`: `url` (str, required), `api_key` (str, required, `no_log`), `api_secret` (str, required, `no_log`), `validate_certs` (bool, default `True`), `timeout` (int, default 30).
  - `common.client_from_params(params: dict) -> OPNsenseClient`.
  - `common.get_path(data: dict, key: str) -> dict` (follows a dotted key, `"unbound.general"`) and `common.nest(key: str, value: dict) -> dict` (inverse). Dotted keys are the assistant's call, for settings nested below the model's top level.
  - Module `routerops.opnsense.settings` options: connection options, `path` (str, required, e.g. `nodeexporter/general`), `key` (str, required, e.g. `general`), `fields` (dict, required), `actions` (dict, default `{get: get, set: set}`, keys merged over the default), `apply` (str, optional, e.g. `nodeexporter/service/reconfigure`), `write_only_fields` (list of str, default `[]`), `update_write_only` (`on_create` | `always`, default `on_create`), `ordered_fields` (list of str, default `[]`), `separators` (dict of str, default `{}`).
  - Returns: `changed`, `diff` (`{before: {field: value}, after: {field: value}}`, changed fields only), `settings` (the named fields as read before any write, normalised, write-only fields omitted; a playbook registers it to restore the original state).

Behaviour (assistant's call for singletons): write-only fields are not compared; they are sent along with any write, and they force a write only when `update_write_only: always`. The `set` payload holds the changed fields plus the write-only fields, nested under `key`.

- [ ] **Step 1: Write the test harness**

`conftest.py` provides a `FakeClient` (constructor takes `get_response: dict` and `post_responses: dict[str, dict]`; records `calls: list[tuple[str, str, dict | None]]`) and a fixture `run_settings(args: dict, fake: FakeClient, check_mode: bool = False) -> dict` that patches `settings.client_from_params` to return `fake`, adds `_ansible_check_mode` and `_ansible_diff: True`, runs `settings.main()` inside `ansible.module_utils.testing.patch_module_args`, catches `SystemExit` and returns the parsed JSON from stdout.

- [ ] **Step 2: Write the failing tests**

Base args: `path: nodeexporter/general`, `key: general`, `apply: nodeexporter/service/reconfigure`, connection options. Base read: `{"general": {"enabled": "0", "listenport": "9100", "cpu": "1", "secret": ""}}`.

```python
def test_no_change_skips_write_and_apply(...):  # fields {listenport: 9100, cpu: True} -> changed False, calls == [("GET", "nodeexporter/general/get", None)]
def test_change_posts_only_differing_fields_and_applies(...):
    # fields {enabled: True, listenport: 9100} -> changed True
    # POST "nodeexporter/general/set" payload {"general": {"enabled": "1"}}, then POST "nodeexporter/service/reconfigure"
def test_check_mode_does_not_post(...):  # check_mode True -> changed True, no POST call
def test_failed_validation_fails_with_validations(...):
    # set answers {"result": "failed", "validations": {"general.listenport": "bad"}} -> failed True, result["validations"] == that map, no apply call
def test_apply_failure_fails(...):  # reconfigure answers {"status": "failed"} -> failed True
def test_unknown_field_fails(...):  # fields {enabeld: True} -> failed True, "enabeld" in msg, no POST
def test_missing_key_fails(...):  # key "nope" -> failed True, "nope" in msg
def test_no_apply_path_skips_apply(...):  # apply omitted -> only GET and set POST
def test_diff_contains_only_changed_fields(...):  # diff == {"before": {"enabled": False}, "after": {"enabled": True}}
def test_write_only_not_compared(...):  # fields {listenport: 9100, secret: "x"}, write_only_fields [secret] -> changed False, no POST
def test_write_only_sent_with_other_change(...):  # fields {enabled: True, secret: "x"} -> payload {"general": {"enabled": "1", "secret": "x"}}
def test_write_only_always_forces_write(...):  # update_write_only always, nothing else changed -> changed True, payload {"general": {"secret": "x"}}
def test_write_only_absent_from_diff_and_result(...):  # "secret" not in diff before/after, not in result["settings"]
def test_result_settings_are_values_before_write(...):  # fields {enabled: True} -> result["settings"] == {"enabled": False}
def test_actions_override(...):  # actions {get: getSettings} -> GET "nodeexporter/general/getSettings"
def test_dotted_key(...):  # read {"unbound": {"general": {"enabled": "0"}}}, key "unbound.general" -> payload {"unbound": {"general": {"enabled": "1"}}}
```

- [ ] **Step 3: Run to verify they fail**

Run: `make units`
Expected: FAIL, `settings` not importable.

- [ ] **Step 4: Implement `common.py` and `plugins/modules/settings.py`**

`settings.main()` builds `AnsibleModule(argument_spec=<CONNECTION_ARGSPEC merged with the own options via dict(...)>, supports_check_mode=True)`, turns every `OPNsenseError` into `fail_json(msg=..., validations=...)` and a `KeyError` from `field_diff` or `get_path` into `fail_json(msg="field '<name>' not found in '<key>'")` (or `"key '<key>' not found in response"`). Full `DOCUMENTATION` (with `extends_documentation_fragment` not used in plan 1), `EXAMPLES` (node_exporter enable, an Unbound dotted key) and `RETURN`; the docs state that `--diff` prints field values and list the known traps from the spec.

- [ ] **Step 5: Run to verify they pass**

Run: `make check`
Expected: exits 0; `ansible-doc` validation in sanity clean.

- [ ] **Step 6: Add the changelog fragment**

`changelogs/fragments/settings-module.yml` with `major_changes: ["settings - new module to manage OPNsense settings singletons through the MVC API."]`. Run `.venv/bin/antsibull-changelog lint`; expected: no output, exit 0.

- [ ] **Step 7: Commit**

```bash
git add plugins tests/unit/plugins/modules meta/runtime.yml changelogs/fragments
git commit -m "Add settings module for OPNsense settings singletons"
```

### Task 6: CI workflow

Blocked until the owner has created the GitHub org `routerops` and the repository `routerops/opnsense`; steps 1 to 3 run locally before that.

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the workflow**

Triggers: `push` to `main`, `pull_request`. Permissions `contents: read`. Job `check`, `ubuntu-latest`, matrix `ansible-core: ["2.20.10", "2.21.5"]`. Steps: checkout (pinned SHA, `path: ansible_collections/routerops/opnsense`), setup-python 3.12 (pinned SHA), `pip install ansible-core==${{ matrix.ansible-core }} ansible-lint==26.10.1`, `ansible-lint` (2.21.5 only), `ansible-test sanity --docker default`, `ansible-test units --docker default`. Job `secrets`: gitleaks `v8.30.1` binary from its release, `gitleaks git --no-banner`; then `pip install reuse==6.2.0 && reuse lint`. No integration job and no self-hosted runner (spec).

- [ ] **Step 2: Lint the workflow**

Run: `yq '.jobs | keys' .github/workflows/ci.yml && make check`
Expected: `[check, secrets]` printed, `make check` exits 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI for sanity, units, lint and secrets"
```

- [ ] **Step 4: After the owner confirms, add the remote and push**

Ask the owner before pushing. Then `git remote add origin git@github.com:routerops/opnsense.git && git push -u origin main`.
Expected: the `CI` workflow is green for both matrix entries (`gh run watch`).

### Task 7: Integration harness and the first live test

Needs the test VM (owner step). Steps 1 and 2 run without it.

**Files:**
- Create: `tests/integration/settings_nodeexporter.yml`, `docs/testing.md`

**Interfaces:**
- Consumes: Task 5 module and `module_defaults` group `group/routerops.opnsense.opnsense`.

- [ ] **Step 1: Write `docs/testing.md`**

One table each for: the VM (Proxmox, WAN and LAN on bridges without `bridge-ports`, test host on the LAN bridge, plugins `os-acme-client`, `os-node_exporter`, `os-mdns-repeater` installed, snapshot `clean`), the run (`qm rollback <vmid> clean` by hand, then `OPNSENSE_INTEGRATION=1 OPNSENSE_URL=... OPNSENSE_API_KEY=... OPNSENSE_API_SECRET=... make integration`), and the API user's privileges per test, read from the ACL files: `.references/opnsense-plugins/sysutils/node_exporter/src/opnsense/mvc/app/models/OPNsense/NodeExporter/ACL/ACL.xml`. Note that `validate_certs: false` is only for the self-signed test VM.

- [ ] **Step 2: Write `tests/integration/settings_nodeexporter.yml`**

Play on `localhost`, `gather_facts: false`, `module_defaults` for the group with URL, key and secret from `lookup('ansible.builtin.env', ...)`. Tasks, each named in the imperative:

| Task | Assert |
|---|---|
| Run the wanted values in check mode and register `settings` | the original values, kept for the restore |
| Set `enabled: true`, `listenport: 9101`, `cpu: true` | `changed` |
| Set the same values again | `not changed` |
| Set the same values in check mode | `not changed` |
| Set `listenport: 70000` | task fails (`ignore_errors: true`, then assert `failed` and `validations` defined) |
| Restore the saved values | ends the test in the original state |

Expected-fail check (kickoff rule: a check counts only after it failed once): run the second "same values" task once with `listenport: 9102` and see its `not changed` assert fail, then put `9101` back.

- [ ] **Step 3: Run against the VM**

Run: `qm rollback <vmid> clean` (owner), then `OPNSENSE_INTEGRATION=1 ... make integration TARGET=settings_nodeexporter`
Expected: `failed=0`; `make integration` without `OPNSENSE_INTEGRATION=1` exits non-zero with `set OPNSENSE_INTEGRATION=1`.

- [ ] **Step 4: Commit**

```bash
git add tests/integration/settings_nodeexporter.yml docs/testing.md
git commit -m "Add integration harness and node_exporter settings test"
```
