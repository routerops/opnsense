# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import copy
import json

import pytest

from ansible_collections.routerops.opnsense.plugins.module_utils._client import OPNsenseError
from ansible_collections.routerops.opnsense.plugins.modules import item

from .conftest import FakeClient

CONNECTION = {"url": "https://fw.example", "api_key": "test-api-key", "api_secret": "test-api-secret"}
BASE_ARGS = dict(
    CONNECTION,
    path="firewall/alias",
    key="alias",
    lookup=["name"],
    apply="firewall/alias/reconfigure",
    separators={"content": "\n"},
)
SEARCH = "firewall/alias/search_item?rowCount=-1"
TEMPLATE_PATH = "firewall/alias/get_item"
APPLY = "firewall/alias/reconfigure"


def row(uuid, name, description="Web"):
    return {"uuid": uuid, "name": name, "enabled": "1", "content": "192.0.2.1\n192.0.2.2", "description": description}


def alias(name, description="Web"):
    return {
        "alias": {
            "name": name,
            "enabled": "1",
            "type": {"host": {"value": "Host(s)", "selected": 1}},
            "content": {"192.0.2.1": {"selected": 1}, "192.0.2.2": {"selected": 1}, "other": {"selected": 0}},
            "description": description,
            "password": "",
        }
    }


TEMPLATE = {
    "alias": {
        "name": "",
        "enabled": "1",
        "type": {"host": {"value": "Host(s)", "selected": 0}},
        "content": {},
        "description": "",
        "password": "",
    }
}


def fake(rows=None, items=None, post_responses=None):
    rows = [row("u1", "web")] if rows is None else rows
    items = {"u1": alias("web")} if items is None else items
    by_path = {SEARCH: {"rows": rows}, TEMPLATE_PATH: TEMPLATE}
    by_path.update({"%s/%s" % (TEMPLATE_PATH, uuid): data for uuid, data in items.items()})
    deletes = {"firewall/alias/del_item/%s" % r["uuid"]: {"result": "deleted"} for r in rows}
    return FakeClient(None, dict(deletes, **(post_responses or {})), copy.deepcopy(by_path))


def args(*entries, **extra):
    return dict(BASE_ARGS, items=list(entries), **extra)


def present(**fields):
    return {"fields": fields}


def posts(client):
    return [c for c in client.calls if c[0] == "POST"]


def test_unchanged_item_makes_no_write(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", content=["192.0.2.2", "192.0.2.1"])), client)
    assert result["changed"] is False
    assert posts(client) == []
    assert result["outcomes"] == [{"uuid": "u1", "lookup": {"name": "web"}, "action": "unchanged"}]


def test_update_posts_changed_fields_and_applies_once(run_module):
    client = fake(rows=[row("u1", "web"), row("u2", "mail")], items={"u1": alias("web"), "u2": alias("mail")})
    result = run_module(item, args(present(name="web", description="New"), present(name="mail", description="New")), client)
    assert result["changed"] is True
    assert posts(client) == [
        ("POST", "firewall/alias/set_item/u1", {"alias": {"description": "New"}}),
        ("POST", "firewall/alias/set_item/u2", {"alias": {"description": "New"}}),
        ("POST", APPLY, None),
    ]
    assert [i["action"] for i in result["outcomes"]] == ["updated", "updated"]


def test_add_posts_all_fields_and_returns_uuid(run_module):
    client = fake(post_responses={"firewall/alias/add_item": {"result": "saved", "uuid": "u9"}})
    result = run_module(item, args(present(name="mail", content=["192.0.2.5", "192.0.2.6"])), client)
    assert result["changed"] is True
    assert posts(client) == [
        ("POST", "firewall/alias/add_item", {"alias": {"name": "mail", "content": "192.0.2.5\n192.0.2.6"}}),
        ("POST", APPLY, None),
    ]
    assert result["outcomes"] == [{"uuid": "u9", "lookup": {"name": "mail"}, "action": "added"}]


def test_check_mode_add_does_not_post(run_module):
    client = fake()
    result = run_module(item, args(present(name="mail")), client, check_mode=True)
    assert result["changed"] is True
    assert result["outcomes"][0]["uuid"] is None
    assert client.calls == [("GET", SEARCH, None), ("GET", TEMPLATE_PATH, None)]


def test_check_mode_on_empty_search_succeeds(run_module):
    client = fake(rows=[], items={})
    result = run_module(item, args(present(name="mail")), client, check_mode=True)
    assert "failed" not in result
    assert result["outcomes"][0]["action"] == "added"


@pytest.mark.parametrize("check_mode", [False, True])
def test_unknown_field_on_add_fails_before_write(run_module, check_mode):
    client = fake()
    result = run_module(item, args(present(name="mail", descripton="x")), client, check_mode=check_mode)
    assert result["failed"] is True
    assert "descripton" in result["msg"]
    assert posts(client) == []


def test_unknown_field_on_update_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", nope=1)), client)
    assert result["failed"] is True
    assert "nope" in result["msg"]
    assert posts(client) == []


def test_ambiguous_lookup_fails(run_module):
    client = fake(rows=[row("u1", "web"), row("u2", "web")])
    result = run_module(item, args(present(name="web", description="New")), client)
    assert result["failed"] is True
    assert "u1" in result["msg"] and "u2" in result["msg"]
    assert posts(client) == []


def test_duplicate_lookup_in_items_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web"), present(name="web", description="x")), client)
    assert result["failed"] is True
    assert "web" in result["msg"]
    assert client.calls == []


def test_lookup_field_missing_from_item_fails(run_module):
    client = fake()
    result = run_module(item, args(present(description="x")), client)
    assert result["failed"] is True
    assert "name" in result["msg"]
    assert client.calls == []


def test_lookup_field_missing_from_rows_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", descr="x"), lookup=["descr"]), client)
    assert result["failed"] is True
    assert "descr" in result["msg"]
    assert posts(client) == []


def test_lookup_normalises_values(run_module):
    client = fake()
    result = run_module(item, args(present(enabled=True, name="web"), lookup=["enabled", "name"]), client)
    assert result["outcomes"][0]["uuid"] == "u1"
    assert result["outcomes"][0]["action"] == "unchanged"


DNSMASQ_ARGS = dict(
    CONNECTION,
    path="dnsmasq/settings",
    key="host",
    lookup=["host", "domain"],
    actions={"search": "searchHost", "get": "getHost", "set": "setHost"},
)


def dnsmasq_fake():
    rows = [
        {"uuid": "h1", "host": "a", "domain": "x.test", "descr": ""},
        {"uuid": "h2", "host": "a", "domain": "y.test", "descr": ""},
    ]
    return FakeClient(
        None,
        None,
        {
            "dnsmasq/settings/searchHost?rowCount=-1": {"rows": rows},
            "dnsmasq/settings/getHost/h2": {"host": {"host": "a", "domain": "y.test", "descr": ""}},
        },
    )


def test_composite_lookup(run_module):
    client = dnsmasq_fake()
    result = run_module(item, dict(DNSMASQ_ARGS, items=[present(host="a", domain="y.test", descr="Z")]), client)
    assert result["outcomes"][0]["uuid"] == "h2"
    assert posts(client) == [("POST", "dnsmasq/settings/setHost/h2", {"host": {"descr": "Z"}})]


def test_actions_override(run_module):
    client = dnsmasq_fake()
    run_module(item, dict(DNSMASQ_ARGS, items=[present(host="a", domain="y.test", descr="Z")]), client)
    assert client.calls[0] == ("GET", "dnsmasq/settings/searchHost?rowCount=-1", None)
    assert client.calls[1] == ("GET", "dnsmasq/settings/getHost/h2", None)


def test_unknown_action_key_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web"), actions={"serach": "x"}), client)
    assert result["failed"] is True
    assert "serach" in result["msg"]
    assert client.calls == []


def test_failed_add_shows_validations_and_skips_apply(run_module):
    failed = {"result": "failed", "validations": {"alias.name": "bad"}}
    client = fake(post_responses={"firewall/alias/add_item": failed})
    result = run_module(item, args(present(name="mail")), client)
    assert result["failed"] is True
    assert result["validations"] == {"alias.name": "bad"}
    assert [c[1] for c in posts(client)] == ["firewall/alias/add_item"]


def test_write_only_sent_on_add_only(run_module):
    client = fake()
    entries = [
        {"fields": {"name": "mail"}, "write_only": {"password": "s"}},
        {"fields": {"name": "web"}, "write_only": {"password": "s"}},
    ]
    run_module(item, args(*entries), client)
    assert posts(client) == [
        ("POST", "firewall/alias/add_item", {"alias": {"name": "mail", "password": "s"}}),
        ("POST", APPLY, None),
    ]


def test_write_only_always_forces_set(run_module):
    client = fake()
    entry = {"fields": {"name": "web"}, "write_only": {"password": "s"}}
    result = run_module(item, args(entry, update_write_only="always"), client)
    assert result["changed"] is True
    assert posts(client)[0] == ("POST", "firewall/alias/set_item/u1", {"alias": {"password": "s"}})


def test_write_only_absent_from_diff_and_result(run_module):
    client = fake()
    entries = [
        {"fields": {"name": "mail"}, "write_only": {"password": "s"}},
        {"fields": {"name": "web", "description": "New"}, "write_only": {"password": "s"}},
    ]
    result = run_module(item, args(*entries, update_write_only="always"), client)
    assert "password" not in json.dumps(result["diff"])
    assert "password" not in json.dumps(result["outcomes"])


def test_diff_per_item_label(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", description="New")), client)
    assert result["diff"] == {"before": {"name=web": {"description": "Web"}}, "after": {"name=web": {"description": "New"}}}


def test_item_disappeared_fails(run_module):
    client = fake(items={"u1": []})
    result = run_module(item, args(present(name="web", description="New")), client)
    assert result["failed"] is True
    assert "u1" in result["msg"]
    assert posts(client) == []


def absent(**fields):
    return {"fields": fields, "state": "absent"}


def test_absent_deletes_matched_item(run_module):
    client = fake()
    result = run_module(item, args(absent(name="web")), client)
    assert result["changed"] is True
    assert posts(client) == [("POST", "firewall/alias/del_item/u1", None), ("POST", APPLY, None)]
    assert result["outcomes"] == [{"uuid": "u1", "lookup": {"name": "web"}, "action": "deleted"}]
    assert result["diff"]["before"] == {"name=web": {"name": "web"}}


def test_absent_missing_item_is_unchanged(run_module):
    client = fake()
    result = run_module(item, args(absent(name="mail")), client)
    assert result["changed"] is False
    assert posts(client) == []
    assert result["outcomes"] == [{"uuid": None, "lookup": {"name": "mail"}, "action": "unchanged"}]


def test_absent_not_found_counts_as_gone(run_module):
    client = fake(post_responses={"firewall/alias/del_item/u1": {"result": "not found"}})
    result = run_module(item, args(absent(name="web")), client)
    assert "failed" not in result


def test_absent_check_mode_does_not_post(run_module):
    client = fake()
    result = run_module(item, args(absent(name="web")), client, check_mode=True)
    assert result["changed"] is True
    assert posts(client) == []


def test_delete_in_use_fails_with_message(run_module):
    client = fake()

    def refuse(path, payload=None):
        raise OPNsenseError("POST https://fw.example/api/%s failed with HTTP 500: Cannot delete alias web. Currently in use by x" % path)

    client.post = refuse
    result = run_module(item, args(absent(name="web")), client)
    assert result["failed"] is True
    assert "Cannot delete alias" in result["msg"]


def two_rows():
    return fake(rows=[row("u1", "web"), row("u2", "mail")], items={"u1": alias("web"), "u2": alias("mail")})


def test_purge_deletes_unlisted_rows(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web"), purge=True), client)
    assert result["changed"] is True
    assert posts(client) == [("POST", "firewall/alias/del_item/u2", None), ("POST", APPLY, None)]
    assert result["purged"] == ["u2"]
    assert result["diff"]["before"] == {"name=mail (u2)": {"name": "mail"}}


def test_purge_keeps_absent_listed_rows_out_of_purged(run_module):
    client = two_rows()
    result = run_module(item, args(absent(name="web"), purge=True), client)
    assert result["outcomes"][0]["action"] == "deleted"
    assert result["purged"] == ["u2"]


def test_purge_check_mode_lists_without_deleting(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web"), purge=True), client, check_mode=True)
    assert result["changed"] is True
    assert result["purged"] == ["u2"]
    assert posts(client) == []


def test_purge_nothing_to_delete_is_unchanged(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web"), present(name="mail"), purge=True), client)
    assert result["changed"] is False
    assert result["purged"] == []


def test_absent_not_found_is_unchanged(run_module):
    client = fake(post_responses={"firewall/alias/del_item/u1": {"result": "not found"}})
    result = run_module(item, args(absent(name="web")), client)
    assert result["changed"] is False
    assert result["outcomes"][0]["action"] == "unchanged"
    assert [c[1] for c in posts(client)] == ["firewall/alias/del_item/u1"]


def test_purge_not_found_row_is_not_purged(run_module):
    client = two_rows()
    client.post_responses["firewall/alias/del_item/u2"] = {"result": "not found"}
    result = run_module(item, args(present(name="web"), purge=True), client)
    assert result["changed"] is False
    assert result["purged"] == []
    assert result["diff"]["before"] == {}


def test_unknown_field_on_later_update_fails_before_any_write(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web", description="New"), present(name="mail", nope=1)), client)
    assert result["failed"] is True
    assert "nope" in result["msg"]
    assert posts(client) == []


def test_rejected_later_write_names_saved_items(run_module):
    client = two_rows()
    client.post_responses["firewall/alias/set_item/u2"] = {"result": "failed", "validations": {"alias.description": "bad"}}
    result = run_module(item, args(present(name="web", description="New"), present(name="mail", description="New")), client)
    assert result["failed"] is True
    assert "name=web" in result["msg"]


def test_purge_without_items_checks_lookup_fields(run_module):
    client = two_rows()
    result = run_module(item, args(purge=True, lookup=["descr"]), client)
    assert result["failed"] is True
    assert "descr" in result["msg"]
    assert posts(client) == []


def test_purge_diff_keeps_rows_with_the_same_label(run_module):
    client = fake(rows=[row("u1", "web"), row("u2", "mail"), row("u3", "mail")])
    client.post_responses["firewall/alias/del_item/u3"] = {"result": "deleted"}
    result = run_module(item, args(present(name="web"), purge=True), client)
    assert result["purged"] == ["u2", "u3"]
    assert len(result["diff"]["before"]) == 2


def test_uncomparable_lookup_value_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", description=5), lookup=["name", "description"]), client)
    assert result["failed"] is True
    assert "description" in result["msg"]
    assert posts(client) == []
