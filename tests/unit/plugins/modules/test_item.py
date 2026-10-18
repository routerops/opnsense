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
U1, U2, U3, U9 = ("00000000-0000-4000-8000-%012d" % n for n in (1, 2, 3, 9))
H1, H2 = ("00000000-0000-4000-8000-%012d" % n for n in (11, 12))


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
    rows = [row(U1, "web")] if rows is None else rows
    items = {U1: alias("web")} if items is None else items
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
    assert result["outcomes"] == [{"uuid": U1, "lookup": {"name": "web"}, "action": "unchanged", "fields": {}}]


def test_update_posts_changed_fields_and_applies_once(run_module):
    client = fake(rows=[row(U1, "web"), row(U2, "mail")], items={U1: alias("web"), U2: alias("mail")})
    result = run_module(item, args(present(name="web", description="New"), present(name="mail", description="New")), client)
    assert result["changed"] is True
    assert posts(client) == [
        ("POST", "firewall/alias/set_item/" + U1, {"alias": {"description": "New"}}),
        ("POST", "firewall/alias/set_item/" + U2, {"alias": {"description": "New"}}),
        ("POST", APPLY, None),
    ]
    assert [i["action"] for i in result["outcomes"]] == ["updated", "updated"]


def test_add_posts_all_fields_and_returns_uuid(run_module):
    client = fake(post_responses={"firewall/alias/add_item": {"result": "saved", "uuid": U9}})
    result = run_module(item, args(present(name="mail", content=["192.0.2.5", "192.0.2.6"])), client)
    assert result["changed"] is True
    assert posts(client) == [
        ("POST", "firewall/alias/add_item", {"alias": {"name": "mail", "content": "192.0.2.5\n192.0.2.6"}}),
        ("POST", APPLY, None),
    ]
    assert result["outcomes"] == [{"uuid": U9, "lookup": {"name": "mail"}, "action": "added", "fields": {}}]


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
    client = fake(rows=[row(U1, "web"), row(U2, "web")])
    result = run_module(item, args(present(name="web", description="New")), client)
    assert result["failed"] is True
    assert U1 in result["msg"] and U2 in result["msg"]
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
    assert result["outcomes"][0]["uuid"] == U1
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
        {"uuid": H1, "host": "a", "domain": "x.test", "descr": ""},
        {"uuid": H2, "host": "a", "domain": "y.test", "descr": ""},
    ]
    return FakeClient(
        None,
        None,
        {
            "dnsmasq/settings/searchHost?rowCount=-1": {"rows": rows},
            "dnsmasq/settings/getHost/" + H2: {"host": {"host": "a", "domain": "y.test", "descr": ""}},
        },
    )


def test_composite_lookup(run_module):
    client = dnsmasq_fake()
    result = run_module(item, dict(DNSMASQ_ARGS, items=[present(host="a", domain="y.test", descr="Z")]), client)
    assert result["outcomes"][0]["uuid"] == H2
    assert posts(client) == [("POST", "dnsmasq/settings/setHost/" + H2, {"host": {"descr": "Z"}})]


def test_actions_override(run_module):
    client = dnsmasq_fake()
    run_module(item, dict(DNSMASQ_ARGS, items=[present(host="a", domain="y.test", descr="Z")]), client)
    assert client.calls[0] == ("GET", "dnsmasq/settings/searchHost?rowCount=-1", None)
    assert client.calls[1] == ("GET", "dnsmasq/settings/getHost/" + H2, None)


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
    assert posts(client)[0] == ("POST", "firewall/alias/set_item/" + U1, {"alias": {"password": "s"}})


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
    client = fake(items={U1: []})
    result = run_module(item, args(present(name="web", description="New")), client)
    assert result["failed"] is True
    assert U1 in result["msg"]
    assert posts(client) == []


def absent(**fields):
    return {"fields": fields, "state": "absent"}


def test_absent_deletes_matched_item(run_module):
    client = fake()
    result = run_module(item, args(absent(name="web")), client)
    assert result["changed"] is True
    assert posts(client) == [("POST", "firewall/alias/del_item/" + U1, None), ("POST", APPLY, None)]
    assert result["outcomes"] == [{"uuid": U1, "lookup": {"name": "web"}, "action": "deleted", "fields": {}}]
    assert result["diff"]["before"] == {"name=web": {"name": "web"}}


def test_absent_missing_item_is_unchanged(run_module):
    client = fake()
    result = run_module(item, args(absent(name="mail")), client)
    assert result["changed"] is False
    assert posts(client) == []
    assert result["outcomes"] == [{"uuid": None, "lookup": {"name": "mail"}, "action": "unchanged", "fields": {}}]


def test_absent_not_found_counts_as_gone(run_module):
    client = fake(post_responses={"firewall/alias/del_item/" + U1: {"result": "not found"}})
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
    return fake(rows=[row(U1, "web"), row(U2, "mail")], items={U1: alias("web"), U2: alias("mail")})


def test_purge_deletes_unlisted_rows(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web"), purge=True), client)
    assert result["changed"] is True
    assert posts(client) == [("POST", "firewall/alias/del_item/" + U2, None), ("POST", APPLY, None)]
    assert result["purged"] == [U2]
    assert result["diff"]["before"] == {"name=mail (" + U2 + ")": {"name": "mail"}}


def test_purge_keeps_absent_listed_rows_out_of_purged(run_module):
    client = two_rows()
    result = run_module(item, args(absent(name="web"), purge=True), client)
    assert result["outcomes"][0]["action"] == "deleted"
    assert result["purged"] == [U2]


def test_purge_check_mode_lists_without_deleting(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web"), purge=True), client, check_mode=True)
    assert result["changed"] is True
    assert result["purged"] == [U2]
    assert posts(client) == []


def test_purge_nothing_to_delete_is_unchanged(run_module):
    client = two_rows()
    result = run_module(item, args(present(name="web"), present(name="mail"), purge=True), client)
    assert result["changed"] is False
    assert result["purged"] == []


def test_absent_not_found_is_unchanged(run_module):
    client = fake(post_responses={"firewall/alias/del_item/" + U1: {"result": "not found"}})
    result = run_module(item, args(absent(name="web")), client)
    assert result["changed"] is False
    assert result["outcomes"][0]["action"] == "unchanged"
    assert [c[1] for c in posts(client)] == ["firewall/alias/del_item/" + U1]


def test_purge_not_found_row_is_not_purged(run_module):
    client = two_rows()
    client.post_responses["firewall/alias/del_item/" + U2] = {"result": "not found"}
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
    client.post_responses["firewall/alias/set_item/" + U2] = {"result": "failed", "validations": {"alias.description": "bad"}}
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
    client = fake(rows=[row(U1, "web"), row(U2, "mail"), row(U3, "mail")])
    client.post_responses["firewall/alias/del_item/" + U3] = {"result": "deleted"}
    result = run_module(item, args(present(name="web"), purge=True), client)
    assert result["purged"] == [U2, U3]
    assert len(result["diff"]["before"]) == 2


def test_uncomparable_lookup_value_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", description=5), lookup=["name", "description"]), client)
    assert result["failed"] is True
    assert "description" in result["msg"]
    assert posts(client) == []


def test_apply_failure_after_write_reports_changed(run_module):
    client = fake(post_responses={
        "firewall/alias/add_item": {"result": "saved", "uuid": U9},
        APPLY: {"status": "failed", "status_msg": "x"},
    })
    result = run_module(item, args(present(name="mail")), client)
    assert result["failed"] is True
    assert result["changed"] is True
    assert "already saved but not applied" in result["msg"]


def test_always_send_rides_along_with_a_change(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", type="host", description="New"), always_send=["type"]), client)
    assert result["changed"] is True
    assert posts(client)[0] == ("POST", "firewall/alias/set_item/" + U1, {"alias": {"description": "New", "type": "host"}})


def test_always_send_alone_does_not_write(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", type="host"), always_send=["type"]), client)
    assert result["changed"] is False
    assert posts(client) == []


def test_always_send_field_not_listed_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", description="New"), always_send=["type"]), client)
    assert result["failed"] is True
    assert "'type'" in result["msg"]
    assert client.calls == []


def with_password(name, password):
    data = alias(name)
    data["alias"]["password"] = password
    return data


def test_secret_change_is_written_but_masked(run_module):
    client = fake(items={U1: with_password("web", "EXAMPLE-old")})
    result = run_module(item, args(present(name="web", password="EXAMPLE-new"), secret_fields=["password"]), client)
    assert result["changed"] is True
    assert posts(client)[0] == ("POST", "firewall/alias/set_item/" + U1, {"alias": {"password": "EXAMPLE-new"}})
    assert result["diff"]["before"]["name=web"]["password"] == "********"
    assert result["diff"]["after"]["name=web"]["password"] == "********"
    assert "EXAMPLE-old" not in json.dumps(result)
    assert "EXAMPLE-new" not in json.dumps(result)


def test_secret_unchanged_is_idempotent(run_module):
    client = fake(items={U1: with_password("web", "EXAMPLE-same")})
    result = run_module(item, args(present(name="web", password="EXAMPLE-same"), secret_fields=["password"]), client)
    assert result["changed"] is False
    assert posts(client) == []


def test_secret_masked_in_add_diff(run_module):
    client = fake(post_responses={"firewall/alias/add_item": {"result": "saved", "uuid": U9}})
    result = run_module(item, args(present(name="mail", password="EXAMPLE-add"), secret_fields=["password"]), client)
    assert result["diff"]["after"]["name=mail"]["password"] == "********"
    assert "EXAMPLE-add" not in json.dumps(result)


def query(**fields):
    return {"fields": fields, "state": "query"}


def test_return_fields_after_add(run_module):
    added = alias("mail")
    added["alias"]["refid"] = "6a1f00"
    template = copy.deepcopy(TEMPLATE)
    template["alias"]["refid"] = ""
    client = fake(items={U1: alias("web"), U9: added},
                  post_responses={"firewall/alias/add_item": {"result": "saved", "uuid": U9}})
    client.get_by_path[TEMPLATE_PATH] = template
    result = run_module(item, args(present(name="mail"), return_fields=["refid"]), client)
    assert result["outcomes"][0]["fields"] == {"refid": "6a1f00"}
    assert ("GET", "firewall/alias/get_item/" + U9, None) in client.calls


def test_return_fields_on_unchanged_item_needs_no_extra_request(run_module):
    client = fake()
    result = run_module(item, args(present(name="web"), return_fields=["type", "description"]), client)
    assert result["outcomes"][0]["fields"] == {"type": "host", "description": "Web"}
    assert [c for c in client.calls if c[1].startswith("firewall/alias/get_item/")] == [("GET", "firewall/alias/get_item/" + U1, None)]


def test_return_fields_after_update_show_new_values(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", description="New"), return_fields=["description"]), client)
    assert result["outcomes"][0]["fields"] == {"description": "New"}


def test_query_found(run_module):
    client = fake()
    result = run_module(item, args(query(name="web"), return_fields=["type"]), client)
    assert result["changed"] is False
    assert posts(client) == []
    assert result["outcomes"] == [{"uuid": U1, "lookup": {"name": "web"}, "action": "queried", "fields": {"type": "host"}}]


def test_query_not_found_does_not_write(run_module):
    client = fake()
    result = run_module(item, args(query(name="mail"), return_fields=["type"]), client)
    assert result["changed"] is False
    assert posts(client) == []
    assert result["outcomes"] == [{"uuid": None, "lookup": {"name": "mail"}, "action": "queried", "fields": {}}]


def test_query_ignores_purge(run_module):
    client = fake(rows=[row(U1, "web"), row(U2, "mail")], items={U1: alias("web"), U2: alias("mail")})
    result = run_module(item, args(query(name="web"), present(name="mail"), purge=True), client)
    assert result["purged"] == []
    assert posts(client) == []


def test_return_field_not_in_model_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web"), return_fields=["refidd"]), client)
    assert result["failed"] is True
    assert "'refidd'" in result["msg"]
    assert posts(client) == []


def test_return_fields_mask_secrets(run_module):
    client = fake(items={U1: with_password("web", "EXAMPLE-ret")})
    result = run_module(item, args(present(name="web"), return_fields=["password"], secret_fields=["password"]), client)
    assert result["outcomes"][0]["fields"] == {"password": "********"}
    assert "EXAMPLE-ret" not in json.dumps(result)


def test_stored_secret_stays_out_of_error_messages(run_module):
    client = fake(items={U1: with_password("web", "EXAMPLE-raw")})
    result = run_module(item, args(present(name="web", password=5), secret_fields=["password"]), client)
    assert result["failed"] is True
    assert "EXAMPLE-raw" not in json.dumps(result)


def test_return_field_container_fails(run_module):
    nested = alias("web")
    nested["alias"]["auth"] = {"user": "u", "psk": "EXAMPLE-psk"}
    template = copy.deepcopy(TEMPLATE)
    template["alias"]["auth"] = {"user": "", "psk": ""}
    client = fake(items={U1: nested})
    client.get_by_path[TEMPLATE_PATH] = template
    result = run_module(item, args(present(name="web"), return_fields=["auth"], secret_fields=["auth.psk"]), client)
    assert result["failed"] is True
    assert "'auth'" in result["msg"]
    assert "EXAMPLE-psk" not in json.dumps(result)


def test_failure_after_saved_add_reports_changed(run_module):
    client = fake(items={U1: alias("web"), U9: {"other": {}}},
                  post_responses={"firewall/alias/add_item": {"result": "saved", "uuid": U9}})
    result = run_module(item, args(present(name="mail"), return_fields=["name"]), client)
    assert result["failed"] is True
    assert result["changed"] is True
    assert "already saved but not applied" in result["msg"]


def test_secret_field_naming_a_container_fails(run_module):
    client = fake()
    result = run_module(item, args(present(name="web", tunnel={"psk": "EXAMPLE-psk"}), secret_fields=["tunnel"]), client)
    assert result["failed"] is True
    assert "'tunnel'" in result["msg"]
    assert "EXAMPLE-psk" not in json.dumps(result)
    assert client.calls == []


def test_secret_lookup_stays_out_of_lookup_errors(run_module):
    rows = [dict(row(U1, "web"), password="EXAMPLE\\raw")]
    client = fake(rows=rows)
    result = run_module(item, args(present(name="web", password=5), lookup=["password"], secret_fields=["password"]), client)
    assert result["failed"] is True
    assert "EXAMPLE" not in result["msg"]


def test_check_mode_add_returns_empty_fields(run_module):
    client = fake()
    result = run_module(item, args(present(name="mail"), return_fields=["name"]), client, check_mode=True)
    assert result["outcomes"][0]["fields"] == {}


def test_always_send_not_required_for_absent_or_query(run_module):
    client = fake(rows=[row(U1, "web"), row(U2, "mail")], items={U1: alias("web"), U2: alias("mail")})
    result = run_module(item, args({"fields": {"name": "web"}, "state": "absent"}, query(name="mail"), always_send=["type"]), client)
    assert result.get("failed") is not True


def test_lookup_ignores_non_mvc_rows(run_module):
    legacy = dict(row("0123456789abcdef0123456789abcdef", "web"), legacy=True)
    client = fake(rows=[legacy], items={}, post_responses={"firewall/alias/add_item": {"result": "saved", "uuid": U9}})
    result = run_module(item, args(present(name="web")), client)
    assert result["outcomes"][0]["action"] == "added"
    assert [c[1] for c in posts(client)] == ["firewall/alias/add_item", APPLY]


def test_purge_skips_non_mvc_rows(run_module):
    rows = [row(U1, "web"), row("WAN_DHCP", "WAN_DHCP"), {"uuid": "automatic_wan_1", "is_automatic": True}]
    client = fake(rows=rows)
    result = run_module(item, args(present(name="web"), purge=True), client)
    assert result["changed"] is False
    assert result["purged"] == []
    assert posts(client) == []


def test_query_finds_row_keyed_by_name(run_module):
    client = fake(rows=[row("bogons", "bogons")], items={"bogons": alias("bogons")})
    result = run_module(item, args(query(name="bogons"), return_fields=["type"]), client)
    assert result["changed"] is False
    assert result["outcomes"] == [{"uuid": "bogons", "lookup": {"name": "bogons"}, "action": "queried", "fields": {"type": "host"}}]


def test_query_prefers_mvc_row_over_non_mvc_row_with_same_lookup(run_module):
    legacy = dict(row("0123456789abcdef0123456789abcdef", "web"), legacy=True)
    client = fake(rows=[row(U1, "web"), legacy])
    result = run_module(item, args(query(name="web")), client)
    assert result["outcomes"][0]["uuid"] == U1


def test_query_skips_non_mvc_row_without_lookup_field(run_module):
    client = fake(rows=[row(U1, "web"), {"uuid": "automatic_wan_1", "is_automatic": True}])
    result = run_module(item, args(query(name="web")), client)
    assert result["outcomes"][0]["uuid"] == U1


def test_query_return_fields_on_unreadable_non_mvc_row_fails(run_module):
    legacy = "0123456789abcdef0123456789abcdef"
    client = fake(rows=[dict(row(legacy, "web"), legacy=True)], items={legacy: []})
    result = run_module(item, args(query(name="web"), return_fields=["type"]), client)
    assert result["failed"] is True
    assert "'%s' is not an MVC item" % legacy in result["msg"]
    assert posts(client) == []


def test_lookup_matches_uppercase_uuid(run_module):
    upper = U1.upper()
    client = fake(rows=[row(upper, "web")], items={upper: alias("web")})
    result = run_module(item, args(present(name="web")), client)
    assert result["changed"] is False
    assert result["outcomes"][0]["uuid"] == upper
