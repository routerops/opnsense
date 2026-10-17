# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import copy
import json

import pytest
from ansible.module_utils.testing import patch_module_args

from ansible_collections.routerops.opnsense.plugins.modules import settings

from .conftest import FakeClient

CONNECTION = {"url": "https://fw.example", "api_key": "test-api-key", "api_secret": "test-api-secret"}
BASE_ARGS = dict(CONNECTION, path="nodeexporter/general", key="general", apply="nodeexporter/service/reconfigure")
BASE_READ = {"general": {"enabled": "0", "listenport": "9100", "cpu": "1", "secret": ""}}


def fake(post_responses=None, read=None):
    return FakeClient(copy.deepcopy(read or BASE_READ), post_responses)


def posts(client):
    return [c for c in client.calls if c[0] == "POST"]


def test_no_change_skips_write_and_apply(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, fields={"listenport": 9100, "cpu": True}), client)
    assert result["changed"] is False
    assert client.calls == [("GET", "nodeexporter/general/get", None)]


def test_change_posts_only_differing_fields_and_applies(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True, "listenport": 9100}), client)
    assert result["changed"] is True
    assert posts(client) == [
        ("POST", "nodeexporter/general/set", {"general": {"enabled": "1"}}),
        ("POST", "nodeexporter/service/reconfigure", None),
    ]


def test_check_mode_does_not_post(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}), client, check_mode=True)
    assert result["changed"] is True
    assert posts(client) == []


def test_failed_validation_fails_with_validations(run_module):
    client = fake({"nodeexporter/general/set": {"result": "failed", "validations": {"general.listenport": "bad"}}})
    result = run_module(settings, dict(BASE_ARGS, fields={"listenport": 70000}), client)
    assert result["failed"] is True
    assert result["validations"] == {"general.listenport": "bad"}
    assert [c[1] for c in posts(client)] == ["nodeexporter/general/set"]


def test_apply_failure_fails(run_module):
    client = fake({"nodeexporter/service/reconfigure": {"status": "failed"}})
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}), client)
    assert result["failed"] is True


def test_unknown_field_fails(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, fields={"enabeld": True}), client)
    assert result["failed"] is True
    assert "enabeld" in result["msg"]
    assert posts(client) == []


def test_missing_key_fails(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, key="nope", fields={"enabled": True}), client)
    assert result["failed"] is True
    assert "nope" in result["msg"]


def test_no_apply_path_skips_apply(run_module):
    client = fake()
    args = dict(BASE_ARGS, fields={"enabled": True})
    del args["apply"]
    run_module(settings, args, client)
    assert [c[1] for c in posts(client)] == ["nodeexporter/general/set"]


def test_diff_contains_only_changed_fields(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True, "listenport": 9100}), fake())
    assert result["diff"] == {"before": {"enabled": False}, "after": {"enabled": True}}


def test_write_only_not_compared(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, fields={"listenport": 9100}, write_only={"secret": "s3cr3t-value"}), client)
    assert result["changed"] is False
    assert posts(client) == []


def test_write_only_sent_with_other_change(run_module):
    client = fake()
    run_module(settings, dict(BASE_ARGS, fields={"enabled": True}, write_only={"secret": "s3cr3t-value"}), client)
    assert posts(client)[0][2] == {"general": {"enabled": "1", "secret": "s3cr3t-value"}}


def test_write_only_always_forces_write(run_module):
    client = fake()
    result = run_module(
        settings,
        dict(BASE_ARGS, fields={"listenport": 9100}, write_only={"secret": "s3cr3t-value"}, update_write_only="always"),
        client,
    )
    assert result["changed"] is True
    assert posts(client)[0][2] == {"general": {"secret": "s3cr3t-value"}}


def test_write_only_absent_from_diff_and_result(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}, write_only={"secret": "s3cr3t-value"}), fake())
    assert "secret" not in result["diff"]["before"]
    assert "secret" not in result["diff"]["after"]
    assert "secret" not in result["settings"]


def test_result_settings_are_values_before_write(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}), fake())
    assert result["settings"] == {"enabled": False}


def test_actions_override(run_module):
    client = fake()
    run_module(settings, dict(BASE_ARGS, fields={"cpu": True}, actions={"get": "getSettings"}), client)
    assert client.calls[0] == ("GET", "nodeexporter/general/getSettings", None)


def test_dotted_key(run_module):
    client = fake(read={"unbound": {"general": {"enabled": "0"}}})
    args = dict(CONNECTION, path="unbound/settings", key="unbound.general", fields={"enabled": True})
    run_module(settings, args, client)
    assert posts(client)[0] == ("POST", "unbound/settings/set", {"unbound": {"general": {"enabled": "1"}}})


def test_write_only_option_is_no_log():
    assert settings.ARGUMENT_SPEC["write_only"]["no_log"] is True


def test_write_only_value_never_in_output(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}, write_only={"secret": "s3cr3t-value"}), fake())
    assert "s3cr3t-value" not in json.dumps(result)


def test_nested_write_only_merges_into_payload(run_module):
    client = fake(read={"general": {"enabled": "0", "auth": {"user": "u", "password": ""}}})
    args = dict(BASE_ARGS, fields={"enabled": True, "auth": {"user": "u"}}, write_only={"auth": {"password": "s3cr3t-value"}})
    run_module(settings, args, client)
    assert posts(client)[0][2] == {"general": {"enabled": "1", "auth": {"password": "s3cr3t-value"}}}


def test_unknown_ordered_field_fails(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"cpu": True}, ordered_fields=["cpus"]), fake())
    assert result["failed"] is True
    assert "cpus" in result["msg"]


def test_unknown_separator_field_fails(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"cpu": True}, separators={"contnet": "\n"}), fake())
    assert result["failed"] is True
    assert "contnet" in result["msg"]


def test_uncomparable_value_fails_with_message(run_module):
    result = run_module(settings, dict(BASE_ARGS, fields={"listenport": 9100}), fake(read={"general": {"listenport": "abc"}}))
    assert result["failed"] is True
    assert "listenport" in result["msg"]


def test_unknown_write_only_field_fails(run_module):
    client = fake()
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}, write_only={"secrte": "s3cr3t-value"}), client)
    assert result["failed"] is True
    assert "secrte" in result["msg"]
    assert posts(client) == []


def test_field_in_fields_and_write_only_fails(run_module):
    client = fake()
    args = dict(BASE_ARGS, fields={"enabled": True, "secret": "plain-value"}, write_only={"secret": "s3cr3t-value"})
    result = run_module(settings, args, client)
    assert result["failed"] is True
    assert "secret" in result["msg"]
    assert posts(client) == []


def test_settings_apply_failure_reports_saved(run_module):
    client = fake({"nodeexporter/service/reconfigure": {"status": "failed", "status_msg": "x"}})
    result = run_module(settings, dict(BASE_ARGS, fields={"enabled": True}), client)
    assert result["failed"] is True
    assert result["changed"] is True
    assert "saved but not applied" in result["msg"]


def run_capturing_params(monkeypatch, capsys, module_args):
    seen = {}

    def build(params):
        seen.update(params)
        return fake()

    monkeypatch.setattr(settings, "client_from_params", build)
    with patch_module_args(dict(module_args, _ansible_check_mode=True)):
        with pytest.raises(SystemExit):
            settings.main()
    capsys.readouterr()
    return seen


def test_connection_from_environment(monkeypatch, capsys):
    monkeypatch.setenv("OPNSENSE_URL", "https://env.example")
    monkeypatch.setenv("OPNSENSE_API_KEY", "env-api-key")
    monkeypatch.setenv("OPNSENSE_API_SECRET", "env-api-secret")
    monkeypatch.setenv("OPNSENSE_VALIDATE_CERTS", "false")
    module_args = {k: v for k, v in BASE_ARGS.items() if k not in CONNECTION}
    seen = run_capturing_params(monkeypatch, capsys, dict(module_args, fields={"enabled": False}))
    assert seen["url"] == "https://env.example"
    assert seen["api_key"] == "env-api-key"
    assert seen["api_secret"] == "env-api-secret"
    assert seen["validate_certs"] is False


def test_argument_wins_over_environment(monkeypatch, capsys):
    monkeypatch.setenv("OPNSENSE_URL", "https://env.example")
    seen = run_capturing_params(monkeypatch, capsys, dict(BASE_ARGS, fields={"enabled": False}))
    assert seen["url"] == "https://fw.example"


def test_settings_secret_masked_in_settings_return(run_module):
    read = {"general": {"enabled": "0", "listenport": "9100", "cpu": "1", "secret": "EXAMPLE-old"}}
    client = fake(read=read)
    result = run_module(settings, dict(BASE_ARGS, fields={"secret": "EXAMPLE-new"}, secret_fields=["secret"]), client)
    assert result["changed"] is True
    assert result["settings"]["secret"] == "********"
    assert result["diff"]["before"]["secret"] == "********"
    assert "EXAMPLE-old" not in json.dumps(result)
    assert "EXAMPLE-new" not in json.dumps(result)


def test_settings_stored_secret_stays_out_of_error_messages(run_module):
    read = {"general": {"enabled": "0", "listenport": "9100", "cpu": "1", "secret": "EXAMPLE-raw"}}
    result = run_module(settings, dict(BASE_ARGS, fields={"secret": 5}, secret_fields=["secret"]), fake(read=read))
    assert result["failed"] is True
    assert "EXAMPLE-raw" not in json.dumps(result)


def test_settings_secret_with_backslash_stays_out_of_error_messages(run_module):
    read = {"general": {"enabled": "0", "listenport": "9100", "cpu": "1", "secret": "EXAMPLE\\raw"}}
    result = run_module(settings, dict(BASE_ARGS, fields={"secret": 5}, secret_fields=["secret"]), fake(read=read))
    assert result["failed"] is True
    assert "EXAMPLE" not in result["msg"]


def test_validate_certs_zero_from_environment(monkeypatch, capsys):
    monkeypatch.setenv("OPNSENSE_VALIDATE_CERTS", "0")
    seen = run_capturing_params(monkeypatch, capsys, dict(BASE_ARGS, fields={"enabled": False}))
    assert seen["validate_certs"] is False


def test_settings_secret_field_naming_a_container_fails(run_module):
    read = {"general": {"enabled": "0", "tunnel": {"psk": "EXAMPLE-old"}}}
    result = run_module(settings, dict(BASE_ARGS, fields={"tunnel": {"psk": "EXAMPLE-new"}}, secret_fields=["tunnel"]), fake(read=read))
    assert result["failed"] is True
    assert "'tunnel'" in result["msg"]
    assert "EXAMPLE" not in json.dumps(result)
