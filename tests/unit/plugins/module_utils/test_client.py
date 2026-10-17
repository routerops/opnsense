# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import http.client
import io
import json
import urllib.error

import pytest

from ansible_collections.routerops.opnsense.plugins.module_utils import _client as client
from ansible_collections.routerops.opnsense.plugins.module_utils._client import (
    OPNsenseClient,
    OPNsenseError,
    require_deleted,
    require_ok,
    require_saved,
)


class FakeResponse:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body


class FakeOpenUrl:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append(dict(kwargs, url=url))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


def http_error(code, body=b""):
    return urllib.error.HTTPError("https://fw.example/api/x", code, "err", {}, io.BytesIO(body))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(client.time, "sleep", lambda seconds: None)


def install(monkeypatch, *outcomes):
    fake = FakeOpenUrl(*outcomes)
    monkeypatch.setattr(client, "open_url", fake)
    return fake


def test_get_builds_url_and_basic_auth(monkeypatch):
    fake = install(monkeypatch, b'{"general": {}}')
    assert OPNsenseClient("https://fw.example", "k", "s").get("nodeexporter/general/get") == {"general": {}}
    call = fake.calls[0]
    assert call["url"] == "https://fw.example/api/nodeexporter/general/get"
    assert call["method"] == "GET"
    assert call["url_username"] == "k"
    assert call["url_password"] == "s"
    assert call["force_basic_auth"] is True
    assert call["validate_certs"] is True


def test_post_sends_json_body(monkeypatch):
    fake = install(monkeypatch, b'{"result": "saved"}')
    OPNsenseClient("https://fw.example", "k", "s").post("x/y/set", {"a": "1"})
    call = fake.calls[0]
    assert call["method"] == "POST"
    assert json.loads(call["data"]) == {"a": "1"}
    assert call["headers"]["Content-Type"] == "application/json"


def test_post_without_payload_sends_empty_object(monkeypatch):
    fake = install(monkeypatch, b'{"status": "ok"}')
    OPNsenseClient("https://fw.example", "k", "s").post("x/service/reconfigure")
    assert json.loads(fake.calls[0]["data"]) == {}


def test_trailing_slash_in_url_is_ignored(monkeypatch):
    fake = install(monkeypatch, b"{}")
    OPNsenseClient("https://fw.example/", "k", "s").get("a/b/get")
    assert fake.calls[0]["url"] == "https://fw.example/api/a/b/get"


def test_http_error_raises_with_status(monkeypatch):
    install(monkeypatch, http_error(403))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("a/b/get")
    assert e.value.status == 403


def test_non_json_response_raises(monkeypatch):
    install(monkeypatch, b"<html>login</html>")
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("a/b/get")
    assert "https://fw.example/api/a/b/get" in e.value.msg


def test_not_found_names_path(monkeypatch):
    install(monkeypatch, http_error(404))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("nodeexporter/general/get")
    assert e.value.status == 404
    assert "nodeexporter/general/get" in e.value.msg
    assert "plugin" in e.value.msg


def test_endpoint_not_found_body_names_path(monkeypatch):
    install(monkeypatch, b'{"errorMessage": "Endpoint not found"}')
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("nodeexporter/general/get")
    assert e.value.status == 404
    assert "nodeexporter/general/get" in e.value.msg
    assert "plugin" in e.value.msg


def test_get_retries_three_times_on_5xx(monkeypatch):
    fake = install(monkeypatch, http_error(502), http_error(502), b'{"ok": 1}')
    assert OPNsenseClient("https://fw.example", "k", "s").get("a/b/get") == {"ok": 1}
    assert len(fake.calls) == 3


def test_get_gives_up_after_three_attempts(monkeypatch):
    fake = install(monkeypatch, http_error(502), http_error(502), http_error(502), http_error(502))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("a/b/get")
    assert e.value.status == 502
    assert len(fake.calls) == 3


def test_get_retries_on_connection_error(monkeypatch):
    fake = install(monkeypatch, urllib.error.URLError("refused"), b"{}")
    OPNsenseClient("https://fw.example", "k", "s").get("a/b/get")
    assert len(fake.calls) == 2


def test_post_never_retries(monkeypatch):
    fake = install(monkeypatch, http_error(502), b"{}")
    with pytest.raises(OPNsenseError):
        OPNsenseClient("https://fw.example", "k", "s").post("a/b/set", {})
    assert len(fake.calls) == 1


def test_require_saved_accepts_saved():
    require_saved({"result": "saved"})


def test_require_saved_raises_with_validations():
    with pytest.raises(OPNsenseError) as e:
        require_saved({"result": "failed", "validations": {"general.listenport": "bad"}})
    assert e.value.validations == {"general.listenport": "bad"}
    assert e.value.msg == "write rejected by OPNsense: failed"


def test_require_ok_accepts_any_case_and_whitespace():
    require_ok({"status": "OK"})
    require_ok({"status": " ok\n"})


def test_require_ok_raises_with_status_msg():
    with pytest.raises(OPNsenseError) as e:
        require_ok({"status": "failed", "status_msg": "boom"})
    assert "boom" in e.value.msg


def test_get_retries_on_timeout(monkeypatch):
    fake = install(monkeypatch, TimeoutError("read timed out"), b"{}")
    OPNsenseClient("https://fw.example", "k", "s").get("a/b/get")
    assert len(fake.calls) == 2


def test_remote_disconnect_raises_opnsense_error(monkeypatch):
    install(monkeypatch, http.client.RemoteDisconnected("closed"))
    with pytest.raises(OPNsenseError):
        OPNsenseClient("https://fw.example", "k", "s").post("a/b/set", {})


def test_require_saved_rejects_non_dict():
    with pytest.raises(OPNsenseError):
        require_saved([])


def test_require_ok_rejects_non_dict():
    with pytest.raises(OPNsenseError):
        require_ok("done")


def test_http_error_shows_error_message(monkeypatch):
    body = b'{"errorMessage": "Cannot delete alias a. Currently in use by x", "errorTitle": "Alias in use"}'
    install(monkeypatch, http_error(500, body))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").post("firewall/alias/del_item/u1")
    assert "Cannot delete alias a" in e.value.msg
    assert e.value.status == 500


def test_http_error_without_json_body_keeps_code(monkeypatch):
    install(monkeypatch, http_error(500, b"<html>"))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").post("firewall/alias/del_item/u1")
    assert "HTTP 500" in e.value.msg


def test_require_deleted_accepts_deleted_and_not_found():
    require_deleted({"result": "deleted"})
    require_deleted({"result": "not found"})


def test_require_deleted_raises_on_failed():
    with pytest.raises(OPNsenseError) as e:
        require_deleted({"result": "failed"})
    assert "failed" in e.value.msg


def test_http_error_with_broken_body_keeps_code(monkeypatch):
    error = http_error(500)

    def broken_read(*args):
        raise http.client.IncompleteRead(b"")

    error.read = broken_read
    install(monkeypatch, error)
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").post("firewall/alias/del_item/u1")
    assert "HTTP 500" in e.value.msg


def test_401_names_the_credentials(monkeypatch):
    install(monkeypatch, http_error(401, b'{"status": 401, "message": "Authentication Failed"}'))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("firewall/alias/search_item")
    assert "authentication failed" in e.value.msg
    assert "api_key and api_secret" in e.value.msg
    assert e.value.status == 401


def test_403_names_the_privilege(monkeypatch):
    install(monkeypatch, http_error(403, b'{"status": 403, "message": "Forbidden"}'))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("firewall/alias/search_item")
    assert "is forbidden" in e.value.msg
    assert "privilege for firewall/alias/search_item" in e.value.msg


def test_error_title_joins_message(monkeypatch):
    body = b'{"errorMessage": "alias in use by: rule 1", "errorTitle": "Item in use by"}'
    install(monkeypatch, http_error(500, body))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").post("firewall/alias/del_item/u1")
    assert "Item in use by: alias in use by: rule 1" in e.value.msg


def test_validations_list_passes_through():
    with pytest.raises(OPNsenseError) as e:
        require_saved({"result": "failed", "validations": {"alias.name": ["a", "b"]}})
    assert e.value.validations == {"alias.name": ["a", "b"]}


def test_error_messages_hide_url_credentials(monkeypatch):
    install(monkeypatch, http_error(401, b'{"status": 401, "message": "Authentication Failed"}'))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://u:EXAMPLE-pw@fw.example", "k", "s").get("firewall/alias/search_item")
    assert "EXAMPLE-pw" not in e.value.msg
    assert "https://fw.example/api/firewall/alias/search_item" in e.value.msg


def test_403_points_to_the_area_pages(monkeypatch):
    install(monkeypatch, http_error(403, b'{"status": 403, "message": "Forbidden"}'))
    with pytest.raises(OPNsenseError) as e:
        OPNsenseClient("https://fw.example", "k", "s").get("core/firmware/info")
    assert "docs/areas" in e.value.msg
