# Plan 2: `item` module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A working `routerops.opnsense.item` module (lookup by one or several fields, `actions`, `state: absent`, `purge`, `write_only`, returned identifiers, one apply per call), proven live against Dnsmasq hosts and firewall aliases on OPNsense 26.7.

**Architecture:** `item` reuses the plan 1 `module_utils` (`_client.py`, `_fields.py`, `_common.py`). It searches once, matches listed items against the search rows by their lookup fields, reads each matched item with the get action, compares with `field_diff`, then adds, sets or deletes, and applies once at the end. Field-name checks shared with `settings` move into `_fields.py`.

**Tech Stack:** as plan 1 (ansible-core 2.21.5, Python 3.12, ansible-test, ansible-lint 26.10.1, antsibull-changelog 0.35.1).

**Spec:** `docs/superpowers/specs/2026-10-17-routerops-opnsense-design.md`. Tracking: `docs/superpowers/plans/2026-10-17-v0-tracking.md`. Depends on plan 1.

## Global Constraints

- Everything from plan 1's Global Constraints and `AGENTS.md` holds: licences per directory with SPDX headers, exact pins, `result == "saved"` / `"deleted"` and `status` `ok`, check mode never writes, `changed` only on a real write, one apply per call only after a write, zero comments by default, FQCN, English.
- API facts, read from `opnsense/core` `stable/26.7` (`ApiMutableModelControllerBase.php`, `UIModelGrid.php`, `www/api.php`):
  - `addBase` answers `{"result": "saved", "uuid": "<uuid>"}`; `delBase` answers `"deleted"`, `"not found"` or `"failed"`; `setBase` answers `"saved"` or `"failed"` with `validations`.
  - `getBase` with a UUID answers `{<key>: {...}}`, with an unknown UUID `[]`, without a UUID the defaults of a new item (`Add()` without save).
  - Search rows carry `uuid`, each field's raw stored value under its flat name (`source.network` for nested fields), and the display text under `%<name>` when it differs; `rowCount` defaults to `-1` (all rows); the `$fields` argument of `searchBase` only limits which fields a search phrase matches, so every row carries every flat field, secrets included (OpenVPN static key `key`), and the module never prints rows; only a controller that rewrites rows itself changes their content (alias `content` for `authgroup`).
  - `setNodes` (`BaseField.php`) walks the model's own fields and silently ignores any posted key the model lacks.
  - A `UserException` (alias in use, safe delete) answers HTTP 500 with `{"errorMessage": ..., "errorTitle": ...}`.
- Dnsmasq hosts (`dnsmasq/settings`): actions `searchHost`, `getHost`, `addHost`, `setHost`, `delHost`; item key `host`; fields include `host`, `domain`, `ip`, `hwaddr`, `aliases`, `descr`; apply `dnsmasq/service/reconfigure`; privilege `page-services-dnsforwarder`.
- Firewall aliases (`firewall/alias`): default `*Item` actions; item key `alias`; fields include `enabled`, `name`, `type`, `content` (newline-separated, read back as an option map), `description`; apply `firewall/alias/reconfigure` (answers `{"status": "ok"}`); privilege `page-firewall-alias-edit`. `AliasField::getStaticChildren()` adds the built-in aliases (`static_aliases/*.json`, the `__<if>_network` aliases, captive portal aliases) to the model, so the alias search lists them.
- Test fixtures use invented values only (`example.test`, `192.0.2.0/24`, `02:00:00:00:00:xx`).

## Review Focus

- `purge: true` against an area whose search lists items the caller never created: expect deletion only of rows no listed item matched, and every deletion listed in `purged` and in check mode before it happens (Task 4, `test_purge_check_mode_lists_without_deleting`).
- Deleting an alias that a rule still uses: expect a failed task that shows OPNsense's `errorMessage`, not a bare "HTTP 500" (Task 1, `test_http_error_shows_error_message`; Task 4, `test_delete_in_use_fails_with_message`).
- A misspelled field name on a new item (OPNsense's `setNodes` ignores unknown keys, so the add would answer `saved`): expect the task to fail naming the field before any write, also in check mode (Task 3, `test_unknown_field_on_add_fails_before_write`).
- Two existing items with the same lookup value: expect a failed task naming the value and both UUIDs, never a guess (Task 3, `test_ambiguous_lookup_fails`).
- A lookup value typed differently from the stored one (`true` vs `"1"`, a list in another order): expect a match, not a duplicate add (Task 3, `test_lookup_normalises_values`).

---

### Task 1: Client error messages and delete results

**Files:**
- Modify: `plugins/module_utils/_client.py`
- Test: `tests/unit/plugins/module_utils/test_client.py`
- Create: `changelogs/fragments/api-error-message.yml`

**Interfaces:**
- Produces:
  - `_client.require_deleted(response: dict) -> None`: passes on `result` `"deleted"` or `"not found"`, else raises `OPNsenseError("delete rejected by OPNsense: <result>")`.
  - An HTTP error whose body is JSON with `errorMessage` raises `OPNsenseError` whose `msg` ends with `: <errorMessage>`; `status` stays the HTTP code. The 404 handling is unchanged.

- [ ] **Step 1: Write the failing tests**

```python
def test_http_error_shows_error_message(...):
    # open_url raises HTTPError 500 with body b'{"errorMessage": "Cannot delete alias a. Currently in use by x", "errorTitle": "Alias in use"}'
    # -> OPNsenseError, "Cannot delete alias a" in e.msg, e.status == 500
def test_http_error_without_json_body_keeps_code(...):  # body b"<html>" -> "HTTP 500" in e.msg
def test_require_deleted_accepts_deleted_and_not_found(...):  # {"result": "deleted"}, {"result": "not found"} -> no raise
def test_require_deleted_raises_on_failed(...):  # {"result": "failed"} -> OPNsenseError, "failed" in e.msg
```

- [ ] **Step 2: Run to verify they fail**

Run: `make units`
Expected: FAIL, `require_deleted` not importable and the message assert fails.

- [ ] **Step 3: Implement in `plugins/module_utils/_client.py`**

Read the body from the `HTTPError` (`e.read()`), parse it with `json.loads` inside a `try`, append `errorMessage` when present. `require_deleted` sits next to `require_saved`.

- [ ] **Step 4: Run to verify they pass**

Run: `make check`
Expected: exits 0.

- [ ] **Step 5: Add the fragment and commit**

`changelogs/fragments/api-error-message.yml`: `minor_changes: ["settings - a request OPNsense rejects with an error now shows OPNsense's error message."]`.

```bash
git add plugins/module_utils/_client.py tests/unit/plugins/module_utils/test_client.py changelogs/fragments/api-error-message.yml
git commit -m "Show OPNsense error messages and accept delete results"
```

### Task 2: Shared field-name checks

**Files:**
- Modify: `plugins/module_utils/_fields.py`, `plugins/modules/settings.py`
- Test: `tests/unit/plugins/module_utils/test_fields.py`

**Interfaces:**
- Produces:
  - `_fields.flatten(wanted: dict, prefix: str = "") -> dict`: moved unchanged from `settings.py` (`{"a": {"b": 1}}` -> `{"a.b": 1}`).
  - `_fields.check_names(compared: dict, write_only: dict, ordered_fields: list, separators: dict) -> None`: raises `ValueError` with the exact messages `settings` uses today: `"field '<names>' is in both fields and write_only"`, `"unknown field '<names>' in ordered_fields"`, `"unknown field '<names>' in separators"` (names sorted, joined with `"', '"`). `write_only` is passed already flattened.
- `settings.main()` calls `check_names` and turns its `ValueError` into `fail_json(msg=str(e))`; its behaviour and tests stay unchanged.

- [ ] **Step 1: Write the failing tests**

```python
def test_flatten_nested(...):  # {"source": {"network": "x", "port": 1}, "a": 2} -> {"source.network": "x", "source.port": 1, "a": 2}
def test_check_names_overlap(...):  # compared {"a": 1, "s": ""}, write_only {"s": "x"} -> ValueError "field 's' is in both fields and write_only"
def test_check_names_unknown_ordered(...):  # ordered ["nope"] -> ValueError "unknown field 'nope' in ordered_fields"
def test_check_names_accepts_write_only_separator(...):  # separators {"s": "\n"}, write_only {"s": "x"} -> no raise
```

- [ ] **Step 2: Run to verify they fail**

Run: `make units`
Expected: FAIL, `flatten` and `check_names` not importable from `fields`.

- [ ] **Step 3: Move `flatten`, add `check_names`, call both from `settings.py`**

- [ ] **Step 4: Run to verify they pass**

Run: `make check`
Expected: exits 0; every `test_settings.py` test passes unchanged.

- [ ] **Step 5: Commit**

```bash
git add plugins/module_utils/_fields.py plugins/modules/settings.py tests/unit/plugins/module_utils/test_fields.py
git commit -m "Share field-name checks between modules"
```

### Task 3: `item` module: lookup, add, update

**Files:**
- Create: `plugins/modules/item.py`, `tests/unit/plugins/modules/test_item.py`, `changelogs/fragments/item-module.yml`
- Modify: `tests/unit/plugins/modules/conftest.py`, `meta/runtime.yml` (add `item` to the `opnsense` action group)

**Interfaces:**
- Consumes: Task 1 `require_deleted`; Task 2 `flatten`, `check_names`; plan 1 `field_diff`, `nest_fields`, `normalize`, `to_api`, `get_path`, `nest`, `CONNECTION_ARGSPEC`, `client_from_params`, `require_saved`, `require_ok`, `OPNsenseError`.
- Produces, module `routerops.opnsense.item` (option names are the assistant's call where the spec leaves them open):

| Option | Type | Default | Meaning |
|---|---|---|---|
| connection options | | | as `settings` |
| `path` | str, required | | controller base path, `firewall/alias` |
| `key` | str, required | | item key in get and write payloads, `alias`; dotted keys allowed as in `settings` |
| `items` | list of dict, required | | each: `fields` (dict, required), `write_only` (dict, default `{}`, `no_log=True`), `state` (`present` \| `absent`, default `present`) |
| `lookup` | list of str | `[description]` | fields forming the lookup key; each must be in every item's `fields` |
| `actions` | dict | `{}` | merged over `{search: search_item, get: get_item, add: add_item, set: set_item, del: del_item}`; an unknown action key fails |
| `apply` | str | | action path run once after any write |
| `purge` | bool | `false` | Task 4 |
| `update_write_only` | `on_create` \| `always` | `on_create` | `always` sends write-only values on every run of a matched item and reports `changed` |
| `ordered_fields`, `separators` | | `[]`, `{}` | as `settings`, for all items; names are not checked against the fields, so the values can come from `module_defaults` or the catalog and apply to items that do not name the field |

- Returns: `changed`; `outcomes` (validate-modules rejects `items` as a return key, since Jinja dot access hits `dict.items`): one entry per listed item in input order, `{"uuid": str | None, "lookup": {field: wanted value}, "action": "added" | "updated" | "deleted" | "unchanged"}` (`uuid` is `None` for an item added in check mode or absent and not found); `purged`: list of UUIDs (Task 4); `diff`: `{before: {label: {...}}, after: {label: {...}}}` where `label` is `"<f>=<v>"` per lookup field joined with `,`; an added item has only `after` (its compared fields), an updated item the changed fields on both sides, a deleted item only `before` (its lookup fields).

Flow, which the tests pin:
1. Option checks before any request: `check_names` per item for the `fields`/`write_only` overlap only; every lookup field in every item's `fields`; lookup values unique among listed items (compare the `_comparable` form) -> `"duplicate lookup value '<label>' in items"`.
2. `GET <path>/<search>?rowCount=-1`; `rows = response["rows"]`.
3. Match each item: a row matches when, for every lookup field, `normalize(row[field], wanted, ...) == ` the wanted comparable value. A row without the lookup field fails `"lookup field '<f>' not in the search results of '<path>'"`. A lookup value that cannot be compared with the stored one fails naming the field. More than one match fails `"lookup '<label>' matches several items: <uuid>, <uuid>"`.
4. When any present item is unmatched: `GET <path>/<get>` (no UUID) once as the template; run `field_diff(template_section, fields)` and `get_path` for each write-only name only to catch unknown names (`"field '<name>' not found in '<key>'"`). This also runs in check mode.
5. Matched present item: `GET <path>/<get>/<uuid>` for every matched item before the first write, so a bad field name fails before anything is saved; a response without `key` fails `"item <uuid> disappeared during the run"`; `field_diff` -> changed fields; write when changes exist or `write_only` is set and `update_write_only == "always"`; payload `nest(key, nest_fields(changed fields + write_only))` to `POST <path>/<set>/<uuid>`, `require_saved`.
6. Unmatched present item: payload `nest(key, nest_fields(all fields + write_only))` to `POST <path>/<add>`, `require_saved`, `uuid` from the response.
7. After all items (and Task 4's deletes): `POST <apply>` with `require_ok` when any write happened and `apply` is set. Check mode skips every POST. A write rejected after earlier saves fails naming the items already saved but not applied.

- [ ] **Step 1: Extend the test harness**

`FakeClient.__init__(get_response, post_responses=None, get_by_path=None)`: `get(path)` returns `get_by_path[path]` when present, else `get_response`. `post_responses` values may be a list, consumed in order (two adds to the same path). `test_settings.py` keeps working unchanged.

- [ ] **Step 2: Write the failing tests**

Base args: `path: firewall/alias`, `key: alias`, `lookup: [name]`, `apply: firewall/alias/reconfigure`, `separators: {content: "\n"}`. Search: `{"rows": [{"uuid": "u1", "name": "web", "enabled": "1", "content": "192.0.2.1\n192.0.2.2", "description": "Web"}]}`. Get `firewall/alias/get_item/u1`: `{"alias": {"name": "web", "enabled": "1", "type": {"host": {"value": "Host(s)", "selected": 1}}, "content": {"192.0.2.1": {"selected": 1}, "192.0.2.2": {"selected": 1}, "other": {"selected": 0}}, "description": "Web"}}`. Template `firewall/alias/get_item`: same keys with empty values.

```python
def test_unchanged_item_makes_no_write(...):  # fields {name: web, content: [192.0.2.2, 192.0.2.1]} -> changed False, no POST, outcomes[0] == {"uuid": "u1", "lookup": {"name": "web"}, "action": "unchanged"}
def test_update_posts_changed_fields_and_applies_once(...):
    # two matched items, both change description -> POST set_item/u1, set_item/u2, then exactly one POST firewall/alias/reconfigure
    # payload {"alias": {"description": "New"}}
def test_add_posts_all_fields_and_returns_uuid(...):  # name "mail" unmatched, add answers {"result": "saved", "uuid": "u9"} -> outcomes[0]["uuid"] == "u9", action "added", payload content "192.0.2.5\n192.0.2.6"
def test_check_mode_add_does_not_post(...):  # unmatched -> changed True, uuid None, only GET calls (search, template)
def test_check_mode_on_empty_search_succeeds(...):  # rows [] -> no failure, action "added"
def test_unknown_field_on_add_fails_before_write(...):  # fields {name: mail, descripton: x} -> failed, "descripton" in msg, no POST; same in check mode
def test_unknown_field_on_update_fails(...):  # matched, fields {name: web, nope: 1} -> failed, "nope" in msg
def test_ambiguous_lookup_fails(...):  # two rows with name "web" -> failed, "u1" and "u2" in msg, no POST
def test_duplicate_lookup_in_items_fails(...):  # two items name "web" -> failed before any GET
def test_lookup_field_missing_from_item_fails(...):  # lookup [name], fields {description: x} -> failed, "name" in msg, no request
def test_lookup_field_missing_from_rows_fails(...):  # lookup [descr] on rows without descr -> failed, "descr" in msg
def test_lookup_normalises_values(...):  # lookup [enabled, name], wanted {enabled: True, name: web} matches row enabled "1"
def test_composite_lookup(...):  # dnsmasq rows {host: a, domain: x.test} and {host: a, domain: y.test}; lookup [host, domain] picks the y.test row
def test_actions_override(...):  # actions {search: searchHost, get: getHost, set: setHost} -> GET dnsmasq/settings/searchHost?rowCount=-1, getHost/<uuid>, POST setHost/<uuid>
def test_unknown_action_key_fails(...):  # actions {serach: x} -> failed, "serach" in msg
def test_failed_add_shows_validations_and_skips_apply(...):  # add answers {"result": "failed", "validations": {"alias.name": "bad"}} -> failed, validations shown, no reconfigure
def test_write_only_sent_on_add_only(...):  # write_only {password: s}: add payload has password; matched unchanged item -> no POST
def test_write_only_always_forces_set(...):  # update_write_only always on matched item -> POST set with {"alias": {"password": "s"}}, changed True
def test_write_only_absent_from_diff_and_result(...):  # "s" appears nowhere in json.dumps(result)
def test_diff_per_item_label(...):  # update description -> diff before {"name=web": {"description": "Web"}}, after {"name=web": {"description": "New"}}
def test_item_disappeared_fails(...):  # get_item/u1 answers [] -> failed, "u1" in msg
```

- [ ] **Step 3: Run to verify they fail**

Run: `make units`
Expected: FAIL, `item` not importable.

- [ ] **Step 4: Implement `plugins/modules/item.py`**

Structure and error handling as `settings.py` (`OPNsenseError` -> `fail_json(msg, validations)`). Full `DOCUMENTATION`, `EXAMPLES` (Dnsmasq host with composite lookup and `actions`; alias with `separators`), `RETURN`. `DOCUMENTATION` states: lookup values must be unique and a multiple match fails; references to other items are UUIDs from an earlier task's return; the module never reorders items (`sequence`); `--diff` prints field values, which can be personal data; the known traps from the spec's "The two modules" (descriptions reject `-`, `type6` must be `none`, an undefined `set_item` answers `saved` and changes nothing, interface assignment is keyed by the interface name); `purge` is documented in Task 4.

- [ ] **Step 5: Run to verify they pass**

Run: `make check`
Expected: exits 0; `ansible-doc` validation in sanity clean.

- [ ] **Step 6: Add the fragment and commit**

`changelogs/fragments/item-module.yml`: `major_changes: ["item - new module to manage OPNsense items (aliases, hosts, rules and others) through the MVC API."]`.

```bash
git add plugins/modules/item.py tests/unit/plugins/modules meta/runtime.yml changelogs/fragments/item-module.yml
git commit -m "Add item module with lookup, add and update"
```

### Task 4: `item` module: delete and purge

**Files:**
- Modify: `plugins/modules/item.py`
- Test: `tests/unit/plugins/modules/test_item.py`

**Interfaces:**
- Consumes: Task 3 flow and return structure; Task 1 `require_deleted`.
- Produces:
  - `state: absent` on a matched item: `POST <path>/<del>/<uuid>`, `require_deleted`, action `"deleted"`; a `"not found"` answer (built-in rows) counts as already gone: action `"unchanged"`, no write; on an unmatched item: no request, action `"unchanged"`, `uuid` `None`.
  - `purge: true`: every search row no listed item (present or absent) matched is deleted after the listed items; its UUID goes to `purged` unless OPNsense answers `"not found"`, its diff `before` entry is keyed `<label> (<uuid>)`, rows are checked for the lookup fields even when `items` is empty, its diff `before` entry carries its lookup fields read from the row. Check mode lists them without deleting.
  - `DOCUMENTATION` for `purge` says it deletes every item the search returns that no listed item matches, recommends a check-mode run first, and notes that some areas list items the caller did not create (the firewall alias search lists the built-in aliases, so `purge` is unusable there).

- [ ] **Step 1: Write the failing tests**

```python
def test_absent_deletes_matched_item(...):  # state absent on "web" -> POST del_item/u1, action "deleted", then reconfigure
def test_absent_missing_item_is_unchanged(...):  # state absent on "mail" -> changed False, no POST
def test_absent_not_found_counts_as_gone(...):  # del answers {"result": "not found"} -> not failed
def test_absent_check_mode_does_not_post(...):  # changed True, no POST
def test_delete_in_use_fails_with_message(...):  # del raises OPNsenseError("... failed with HTTP 500: Cannot delete alias web ...") -> failed, "Cannot delete alias" in msg
def test_purge_deletes_unlisted_rows(...):  # rows u1 web, u2 mail; items [web] + purge -> POST del_item/u2 only, purged == ["u2"], one reconfigure
def test_purge_keeps_absent_listed_rows_out_of_purged(...):  # items [web absent] + purge on rows u1, u2 -> u1 in items as deleted, purged == ["u2"]
def test_purge_check_mode_lists_without_deleting(...):  # purged == ["u2"], changed True, no POST
def test_purge_nothing_to_delete_is_unchanged(...):  # all rows listed and unchanged -> changed False, purged == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `make units`
Expected: FAIL on the new tests only.

- [ ] **Step 3: Implement `state: absent` and `purge` in `plugins/modules/item.py`**

- [ ] **Step 4: Run to verify they pass**

Run: `make check`
Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
git add plugins/modules/item.py tests/unit/plugins/modules/test_item.py
git commit -m "Add delete and purge to the item module"
```

### Task 5: Integration tests for Dnsmasq hosts and firewall aliases

**Files:**
- Create: `tests/integration/test-dnsmasq-host-item.yml`, `tests/integration/test-firewall-alias-item.yml`
- Modify: `docs/testing.md` (privileges table, verified runs)

**Interfaces:**
- Consumes: Task 3 and 4 module; `module_defaults` group `group/routerops.opnsense.opnsense`; `make integration-local TARGET=<name>`.

- [ ] **Step 1: Owner step: grant the privileges and retake the snapshot**

The owner adds `page-services-dnsforwarder` ("Services: Dnsmasq DNS/DHCP: Settings") and `page-firewall-alias-edit` ("Firewall: Alias: Edit") to the API user `ansible-test` and retakes the snapshot `clean` as described in `docs/testing.md`. Add both rows to the privileges table with their sources: `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Dnsmasq/ACL/ACL.xml` and `opnsense-core/src/opnsense/mvc/app/models/OPNsense/Core/ACL/ACL.xml`.

- [ ] **Step 2: Write `tests/integration/test-dnsmasq-host-item.yml`**

Play as in `test-nodeexporter-settings.yml`; `module_defaults` set `path: dnsmasq/settings`, `key: host`, `lookup: [host, domain]`, `actions: {search: searchHost, get: getHost, add: addHost, set: setHost, del: delHost}`, `apply: dnsmasq/service/reconfigure`. Hosts `rt-one` and `rt-two` in domain `example.test`, `ip` `192.0.2.11` and `192.0.2.12`, `descr` `routerops test`. The tasks run in a `block` with an `always` that deletes both hosts:

| Task | Assert |
|---|---|
| Add `rt-one` in check mode | `changed`, `outcomes[0]['uuid'] is none`, not failed |
| Add `rt-one` and `rt-two` | `changed`, both `action == 'added'`, both UUIDs set |
| Add both again | `not changed` |
| Add both again in check mode | `not changed` |
| Change `rt-one` `descr` to `routerops test changed` | `changed`, `outcomes[0]['action'] == 'updated'`, UUID equals the one from the add |
| List only `rt-one` with `purge: true` in check mode | `changed`, `purged` holds `rt-two`'s UUID |
| List only `rt-one` with `purge: true` | `changed`, `purged` holds `rt-two`'s UUID |
| Set `rt-two` `state: absent` | `not changed` |
| Set `rt-one` `state: absent` | `changed`, `action == 'deleted'` |
| Add `rt-one` with `ip: 192.0.2.300` | fails (`ignore_errors: true`), `validations` defined |

- [ ] **Step 3: Write `tests/integration/test-firewall-alias-item.yml`**

`module_defaults`: `path: firewall/alias`, `key: alias`, `lookup: [name]`, `separators: {content: "\n"}`, `apply: firewall/alias/reconfigure`, default actions. Alias `rt_test_hosts`, `type: host`, `content: [192.0.2.21, 192.0.2.22]`, `description: routerops test`; `always` deletes it. No `purge` here: the alias search lists the built-in aliases.

| Task | Assert |
|---|---|
| Add in check mode | `changed`, not failed |
| Add | `changed`, `action == 'added'` |
| Add again with `content` reversed | `not changed` |
| Add again in check mode | `not changed` |
| Add `192.0.2.23` to `content` | `changed`, `action == 'updated'` |
| Delete | `changed`, `action == 'deleted'` |
| Delete again | `not changed` |

- [ ] **Step 4: Prove each idempotency assert fails once**

For each playbook: copy it to the scratchpad, change one wanted value in the "again" task, run it with `ANSIBLE_COLLECTIONS_PATH=$PWD/build .venv/bin/ansible-playbook <copy>` through the tunnel and see the `not changed` assert fail; then `make integration-reset`.

- [ ] **Step 5: Run against the VM**

Run: `make integration-reset`, then `make integration-local TARGET=test-dnsmasq-host-item`, `make integration-local TARGET=test-firewall-alias-item`, and `make integration-local` (all tests, including `test-nodeexporter-settings`).
Expected: `failed=0` in every play (ignored expected failures only).

- [ ] **Step 6: Record and commit**

Add a row per test to "Verified runs" in `docs/testing.md` (date `TT.MM.JJJJ` as in the existing row, OPNsense version, result).

```bash
git add tests/integration/test-dnsmasq-host-item.yml tests/integration/test-firewall-alias-item.yml docs/testing.md
git commit -m "Add item integration tests for Dnsmasq hosts and firewall aliases"
```

- [ ] **Step 7: Update the tracking file**

In `docs/superpowers/plans/2026-10-17-v0-tracking.md` set plan 1 to `done`, plan 2's file name to `2026-10-17-plan-2-item-module.md` and its status to `done`, and record in plan 4's row that the firewall `apply` success text (`FilterBaseController::applyAction` returns raw `configd` output as `status`) is checked in the first filter rule test, since no plan 2 area uses that endpoint. Commit with `git commit -m "Mark plans 1 and 2 done"`.
