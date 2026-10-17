# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import http.client
import io
import json
import urllib.error

import pytest

from ansible_collections.routerops.opnsense.plugins.module_utils import client
from ansible_collections.routerops.opnsense.plugins.module_utils.client import (
    OPNsenseClient,
    OPNsenseError,
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


def http_error(code):
    return urllib.error.HTTPError("https://fw.example/api/x", code, "err", {}, io.BytesIO(b""))


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
