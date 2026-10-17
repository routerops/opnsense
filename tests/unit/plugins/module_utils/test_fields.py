# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.routerops.opnsense.plugins.module_utils.fields import (
    field_diff,
    nest_fields,
    normalize,
    to_api,
)


def test_normalize_bool():
    assert normalize("1", True) is True
    assert normalize("0", True) is False


def test_normalize_int():
    assert normalize("9100", 9100) == 9100
    assert normalize("", 1) is None


def test_normalize_single_option():
    assert normalize({"a": {"value": "A", "selected": 0}, "b": {"value": "B", "selected": 1}}, "b") == "b"


def test_normalize_multi_option():
    assert normalize({"a": {"selected": 1}, "b": {"selected": 1}, "c": {"selected": 0}}, ["a", "b"]) == ["a", "b"]


def test_normalize_list_ignores_order():
    assert field_diff({"x": {"a": {"selected": 1}, "b": {"selected": 1}}}, {"x": ["b", "a"]}) == {}


def test_normalize_comma_string_as_list():
    assert normalize("a,b", ["b", "a"]) == ["a", "b"]


def test_to_api():
    assert [to_api(True), to_api(False), to_api(["a", "b"]), to_api(9100), to_api(None), to_api("x")] == ["1", "0", "a,b", "9100", "", "x"]


def test_field_diff_reports_only_differences():
    assert field_diff({"enabled": "0", "listenport": "9100"}, {"enabled": True, "listenport": 9100}) == {"enabled": (False, True)}


def test_field_diff_missing_field_raises():
    with pytest.raises(KeyError):
        field_diff({"enabled": "0"}, {"enabeld": True})


def test_normalize_empty_select_forms():
    assert normalize([], "") == ""
    assert normalize(None, []) == []
    assert normalize({"": {"value": "none", "selected": 1}, "a": {"selected": 0}}, "") == ""


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
